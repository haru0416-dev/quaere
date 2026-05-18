use anyhow::{Context, Result};
use std::path::PathBuf;

/// Resolve the install target. Falls back to ~/.claude/skills/ when no override is given.
pub fn resolve_target(custom: Option<PathBuf>) -> Result<PathBuf> {
    if let Some(p) = custom {
        return Ok(p);
    }
    let home = dirs::home_dir().context("could not resolve $HOME")?;
    Ok(home.join(".claude").join("skills"))
}

/// Path to the Quaere manifest under a given install target.
pub fn manifest_path(target: &std::path::Path) -> PathBuf {
    target.join(".quaere").join("manifest.json")
}
