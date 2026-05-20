use anyhow::{Context, Result};
use std::path::PathBuf;

/// Default install directory for the Claude Code agent.
pub fn claude_default() -> Result<PathBuf> {
    let home = dirs::home_dir().context("could not resolve $HOME")?;
    Ok(home.join(".claude").join("skills"))
}

/// Default install directory for the Codex CLI agent.
pub fn codex_default() -> Result<PathBuf> {
    let home = dirs::home_dir().context("could not resolve $HOME")?;
    Ok(home.join(".agents").join("skills"))
}

/// Resolve the install target. Falls back to the Claude default when no override is given.
pub fn resolve_target(custom: Option<PathBuf>) -> Result<PathBuf> {
    if let Some(p) = custom {
        return Ok(p);
    }
    claude_default()
}

/// Path to the Quaere manifest under a given install target.
pub fn manifest_path(target: &std::path::Path) -> PathBuf {
    target.join(".quaere").join("manifest.json")
}
