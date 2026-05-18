use anyhow::Result;
use clap::Args as ClapArgs;
use std::fs;
use std::path::PathBuf;

use crate::manifest::Manifest;
use crate::paths;
use crate::skill_meta::check_skill;

#[derive(ClapArgs)]
pub struct Args {
    /// Install target to inspect. Defaults to ~/.claude/skills/.
    #[arg(long, short = 't')]
    target: Option<PathBuf>,
}

pub fn run(args: Args) -> Result<()> {
    let target = paths::resolve_target(args.target)?;
    let manifest_path = paths::manifest_path(&target);

    if !target.is_dir() {
        anyhow::bail!(
            "install target {} does not exist; run `quaere install` first",
            target.display()
        );
    }
    if !manifest_path.is_file() {
        anyhow::bail!(
            "no manifest at {}; the directory was not created by `quaere install`",
            manifest_path.display()
        );
    }

    let manifest = Manifest::read(&manifest_path)?;
    let mut had_issue = false;

    println!("target  {}", target.display());
    println!("version {}", manifest.quaere_version);

    if manifest.quaere_version != env!("CARGO_PKG_VERSION") {
        println!(
            "  note: installed version {} differs from CLI version {} (run `quaere update`)",
            manifest.quaere_version,
            env!("CARGO_PKG_VERSION")
        );
    }

    for name in &manifest.skills {
        let skill_dir = target.join(name);
        if !skill_dir.is_dir() {
            println!("FAIL {}: directory missing on disk", name);
            had_issue = true;
            continue;
        }
        let report = check_skill(&skill_dir)?;
        if report.is_clean() {
            println!("OK   {}", name);
        } else {
            had_issue = true;
            println!("FAIL {}", name);
            for issue in &report.issues {
                println!("       - {}", issue);
            }
        }
    }

    // Orphan detection: directories present on disk that the manifest does not know about.
    let mut orphans = Vec::new();
    for entry in fs::read_dir(&target)? {
        let entry = entry?;
        if !entry.file_type()?.is_dir() {
            continue;
        }
        let entry_name = entry.file_name().to_string_lossy().into_owned();
        if entry_name.starts_with('.') {
            continue;
        }
        if !manifest.skills.contains(&entry_name) {
            orphans.push(entry_name);
        }
    }
    if !orphans.is_empty() {
        println!();
        println!("orphan directories (present on disk, not in manifest):");
        for name in &orphans {
            println!("  - {}", name);
        }
        if orphans.iter().any(|n| n.starts_with("quaere-")) {
            had_issue = true;
        }
    }

    if had_issue {
        anyhow::bail!("doctor found issues; see output above");
    }

    println!();
    println!("all installed Quaere skills are healthy");
    Ok(())
}
