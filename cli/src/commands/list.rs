use anyhow::Result;
use clap::Args as ClapArgs;
use std::path::PathBuf;

use crate::manifest::Manifest;
use crate::paths;

#[derive(ClapArgs)]
pub struct Args {
    /// Install target to inspect. Defaults to ~/.claude/skills/.
    #[arg(long, short = 't')]
    target: Option<PathBuf>,
}

pub fn run(args: Args) -> Result<()> {
    let target = paths::resolve_target(args.target)?;
    let manifest_path = paths::manifest_path(&target);

    if !manifest_path.exists() {
        println!("no Quaere skills installed at {}", target.display());
        println!("run `quaere install` to set them up");
        return Ok(());
    }

    let manifest = Manifest::read(&manifest_path)?;
    println!("target  {}", target.display());
    println!("version {}", manifest.quaere_version);
    if manifest.skills.is_empty() {
        println!("skills  (none recorded)");
    } else {
        println!("skills");
        for name in &manifest.skills {
            let present = target.join(name).is_dir();
            let marker = if present { " " } else { "!" };
            println!("  {} {}", marker, name);
        }
        let missing: Vec<_> = manifest
            .skills
            .iter()
            .filter(|n| !target.join(n).is_dir())
            .collect();
        if !missing.is_empty() {
            eprintln!(
                "warning: {} skill(s) in manifest are missing on disk; run `quaere doctor`",
                missing.len()
            );
        }
    }
    Ok(())
}
