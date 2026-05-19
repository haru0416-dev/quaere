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
    pub fn new(mut skills: Vec<String>) -> Self {
        skills.sort();
        skills.dedup();
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
        // Write to a sibling tmp file and rename to make the swap atomic on
        // POSIX. A mid-write crash leaves the previous manifest intact rather
        // than producing a half-written JSON the next `quaere list` would
        // refuse to parse.
        let tmp = path.with_extension("json.tmp");
        fs::write(&tmp, json).with_context(|| format!("writing {}", tmp.display()))?;
        fs::rename(&tmp, path)
            .with_context(|| format!("renaming {} to {}", tmp.display(), path.display()))?;
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
