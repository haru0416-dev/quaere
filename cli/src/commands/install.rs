use anyhow::{Context, Result};
use clap::{Args as ClapArgs, ValueEnum};
use include_dir::{include_dir, Dir};
use std::fs;
use std::path::{Path, PathBuf};

use crate::manifest::Manifest;
use crate::paths;

static SKILLS: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/skills");

#[derive(ValueEnum, Clone, Debug, PartialEq)]
pub enum Agent {
    /// Claude Code — ~/.claude/skills/
    Claude,
    /// Codex CLI  — ~/.agents/skills/
    Codex,
    /// Both Claude Code and Codex
    All,
}

impl Agent {
    fn targets(&self) -> Result<Vec<(String, PathBuf)>> {
        Ok(match self {
            Agent::Claude => vec![("Claude Code".to_owned(), paths::claude_default()?)],
            Agent::Codex => vec![("Codex".to_owned(), paths::codex_default()?)],
            Agent::All => vec![
                ("Claude Code".to_owned(), paths::claude_default()?),
                ("Codex".to_owned(), paths::codex_default()?),
            ],
        })
    }
}

#[derive(ClapArgs)]
pub struct Args {
    /// Agent to install for. Defaults to `claude`.
    #[arg(value_enum, default_value = "claude")]
    pub agent: Agent,

    /// Overwrite existing skill directories at the target.
    #[arg(long)]
    force: bool,

    /// Only install the named skill. Repeatable.
    #[arg(long)]
    skill: Vec<String>,

    /// Override the install path directly (advanced). Implies --agent=claude target name.
    #[arg(long, short = 't', hide = true)]
    target: Option<PathBuf>,
}

pub fn run(args: Args) -> Result<()> {
    // --target is a hidden escape hatch; it bypasses agent selection.
    let targets: Vec<(String, PathBuf)> = if let Some(p) = args.target {
        vec![("custom".to_owned(), p)]
    } else {
        args.agent.targets()?
    };

    // Validate --skill names up-front against the embedded bundle.
    let available: Vec<String> = SKILLS
        .dirs()
        .filter_map(|d| {
            d.path()
                .file_name()
                .and_then(|n| n.to_str())
                .map(str::to_owned)
        })
        .filter(|n| n.starts_with("quaere-"))
        .collect();

    if !args.skill.is_empty() {
        let unknown: Vec<&String> = args
            .skill
            .iter()
            .filter(|s| !available.contains(s))
            .collect();
        if !unknown.is_empty() {
            anyhow::bail!(
                "unknown skill(s): {}. Available: {}",
                unknown
                    .iter()
                    .map(|s| s.as_str())
                    .collect::<Vec<_>>()
                    .join(", "),
                available.join(", ")
            );
        }
    }

    // Deduplicate targets that resolve to the same real path (e.g. symlinks).
    let mut seen_real: Vec<PathBuf> = Vec::new();
    let mut deduped: Vec<(String, PathBuf)> = Vec::new();
    for (label, path) in &targets {
        let real = fs::canonicalize(path).unwrap_or_else(|_| path.clone());
        if !seen_real.contains(&real) {
            seen_real.push(real);
            deduped.push((label.clone(), path.clone()));
        }
    }

    let multi = deduped.len() > 1;
    let mut all_skill_names: Vec<String> = Vec::new();

    for (label, target) in &deduped {
        if multi {
            println!("--- {} ({})", label, target.display());
        }

        fs::create_dir_all(target)
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
            if dest.exists() && !args.force {
                skipped.push(name);
                continue;
            }
            // include_dir 0.7 ships `Dir::extract`, but its path semantics did not
            // round-trip cleanly with this layout. The hand-rolled extract_dir below
            // is 25 lines of explicit recursion vs reverse-engineering crate internals.
            //
            // Stage the new content under a sibling directory, then swap it into
            // place so the previous skill content stays intact if extract_dir or
            // a later step fails. Without this, --force would remove_dir_all the
            // dest first and a mid-extract crash would leave the manifest in
            // sync with a half-written skill that doctor can only report after
            // the fact.
            atomic_swap_install(entry, target, &name, &dest)?;
            installed.push(name);
        }

        if installed.is_empty() && skipped.is_empty() {
            anyhow::bail!(
                "no Quaere skills matched the request. Available: {}",
                available.join(", ")
            );
        }

        // Merge into any existing manifest (additive across partial installs).
        let manifest_file = paths::manifest_path(target);
        let mut merged: Vec<String> = Vec::new();
        if manifest_file.is_file() {
            let prior = Manifest::read(&manifest_file)?;
            for name in prior.skills {
                if target.join(&name).is_dir() {
                    merged.push(name);
                }
            }
        }
        merged.extend(installed.iter().cloned());
        merged.extend(skipped.iter().cloned());
        let manifest = Manifest::new(merged);
        manifest.write(&manifest_file)?;

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
        if multi {
            println!();
        }

        // Collect skill names for the Commands block (same across targets).
        if all_skill_names.is_empty() {
            let mut names: Vec<String> = installed.iter().chain(skipped.iter()).cloned().collect();
            names.sort();
            all_skill_names = names;
        }
    }

    // Print Commands block once after all targets are done.
    if !all_skill_names.is_empty() {
        println!();
        println!("Commands:");
        for name in &all_skill_names {
            println!("  /{}", name);
        }
    }

    Ok(())
}

/// Install (or overwrite) one skill at `dest` by staging the embedded
/// content in a sibling `.<name>.staging` directory, then renaming the
/// previous content (if any) to `.<name>.backup`, then renaming staging
/// to `dest`. The dest is therefore either the previous complete content
/// or the new complete content at any observable moment; a mid-extract
/// failure cannot leave dest in a half-written state.
fn atomic_swap_install(entry: &Dir<'_>, target: &Path, name: &str, dest: &Path) -> Result<()> {
    let staging = target.join(format!(".{}.staging", name));
    let backup = target.join(format!(".{}.backup", name));

    // Clear any residue from a prior interrupted install before staging again.
    if staging.exists() {
        fs::remove_dir_all(&staging)
            .with_context(|| format!("removing stale staging {}", staging.display()))?;
    }

    if let Err(e) = extract_dir(entry, &staging) {
        // Leave no orphan staging directory behind on failure.
        let _ = fs::remove_dir_all(&staging);
        return Err(e);
    }

    if dest.exists() {
        // Clear any residue from a prior interrupted swap before reusing the path.
        if backup.exists() {
            fs::remove_dir_all(&backup)
                .with_context(|| format!("removing stale backup {}", backup.display()))?;
        }
        fs::rename(dest, &backup)
            .with_context(|| format!("backing up {} to {}", dest.display(), backup.display()))?;
        if let Err(e) = fs::rename(&staging, dest) {
            // Restore the previous content before reporting failure so the
            // caller does not observe a missing dest.
            let _ = fs::rename(&backup, dest);
            let _ = fs::remove_dir_all(&staging);
            return Err(e)
                .with_context(|| format!("renaming {} to {}", staging.display(), dest.display()));
        }
        fs::remove_dir_all(&backup)
            .with_context(|| format!("removing backup {}", backup.display()))?;
    } else {
        fs::rename(&staging, dest)
            .with_context(|| format!("renaming {} to {}", staging.display(), dest.display()))?;
    }

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
