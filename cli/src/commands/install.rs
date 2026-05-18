use anyhow::{Context, Result};
use clap::Args as ClapArgs;
use include_dir::{include_dir, Dir};
use std::fs;
use std::path::{Path, PathBuf};

use crate::manifest::Manifest;
use crate::paths;

static SKILLS: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../skills");

#[derive(ClapArgs)]
pub struct Args {
    /// Install target. Defaults to ~/.claude/skills/.
    #[arg(long, short = 't')]
    target: Option<PathBuf>,

    /// Overwrite existing skill directories at the target.
    #[arg(long)]
    force: bool,

    /// Only install the named skill. Repeatable.
    #[arg(long)]
    skill: Vec<String>,
}

pub fn run(args: Args) -> Result<()> {
    let target = paths::resolve_target(args.target)?;
    fs::create_dir_all(&target)
        .with_context(|| format!("creating install target {}", target.display()))?;

    let mut installed = Vec::new();
    let mut skipped = Vec::new();
    for entry in SKILLS.dirs() {
        let name = entry
            .path()
            .file_name()
            .and_then(|n| n.to_str())
            .map(str::to_owned)
            .unwrap_or_default();
        if !name.starts_with("quaere-") {
            continue;
        }
        if !args.skill.is_empty() && !args.skill.iter().any(|s| s == &name) {
            continue;
        }

        let dest = target.join(&name);
        if dest.exists() {
            if !args.force {
                skipped.push(name);
                continue;
            }
            fs::remove_dir_all(&dest)
                .with_context(|| format!("removing existing {}", dest.display()))?;
        }
        // include_dir 0.7 ships `Dir::extract`, but its path semantics did not
        // round-trip cleanly with this layout (both `entry.extract(&dest)` and
        // `entry.extract(&target)` failed with ENOENT during testing). The
        // hand-rolled `extract_dir` below stays in-place — 25 lines of explicit
        // recursion is cheaper than reverse-engineering crate-internal path math.
        extract_dir(entry, &dest)?;
        installed.push(name);
    }

    if installed.is_empty() && skipped.is_empty() {
        anyhow::bail!(
            "no Quaere skills matched the request. \
             Available: {}",
            SKILLS
                .dirs()
                .filter_map(|d| d.path().file_name().and_then(|n| n.to_str()))
                .filter(|n| n.starts_with("quaere-"))
                .collect::<Vec<_>>()
                .join(", ")
        );
    }

    let manifest = Manifest::new(installed.clone());
    manifest.write(&paths::manifest_path(&target))?;

    for name in &installed {
        println!("installed {}", name);
    }
    for name in &skipped {
        println!(
            "skipped  {} (already present; pass --force to overwrite)",
            name
        );
    }
    println!("target   {}", target.display());

    Ok(())
}

fn extract_dir(dir: &Dir<'_>, dest: &Path) -> Result<()> {
    fs::create_dir_all(dest).with_context(|| format!("creating {}", dest.display()))?;

    for file in dir.files() {
        let rel = file
            .path()
            .strip_prefix(dir.path())
            .context("computing relative path inside embedded skill")?;
        let out = dest.join(rel);
        if let Some(parent) = out.parent() {
            fs::create_dir_all(parent).with_context(|| format!("creating {}", parent.display()))?;
        }
        fs::write(&out, file.contents()).with_context(|| format!("writing {}", out.display()))?;
    }
    for sub in dir.dirs() {
        let rel = sub
            .path()
            .strip_prefix(dir.path())
            .context("computing relative path inside embedded skill")?;
        extract_dir(sub, &dest.join(rel))?;
    }
    Ok(())
}
