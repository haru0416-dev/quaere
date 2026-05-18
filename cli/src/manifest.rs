use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize)]
pub struct Manifest {
    pub quaere_version: String,
    pub skills: Vec<String>,
}

impl Manifest {
    pub fn new(skills: Vec<String>) -> Self {
        Self {
            quaere_version: env!("CARGO_PKG_VERSION").to_string(),
            skills,
        }
    }

    pub fn write(&self, path: &Path) -> Result<()> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .with_context(|| format!("creating manifest directory {}", parent.display()))?;
        }
        let json = serde_json::to_string_pretty(self)? + "\n";
        fs::write(path, json).with_context(|| format!("writing manifest to {}", path.display()))?;
        Ok(())
    }

    pub fn read(path: &Path) -> Result<Self> {
        let raw = fs::read_to_string(path)
            .with_context(|| format!("reading manifest at {}", path.display()))?;
        let manifest: Manifest = serde_json::from_str(&raw)
            .with_context(|| format!("parsing manifest at {}", path.display()))?;
        Ok(manifest)
    }
}
