use anyhow::{Context, Result};
use clap::Args as ClapArgs;
use serde::Deserialize;
use std::time::Duration;

const DEFAULT_REPO: &str = "haru0416-dev/quaere";

#[derive(ClapArgs)]
pub struct Args {
    /// GitHub repository to check against (owner/name).
    #[arg(long, default_value = DEFAULT_REPO)]
    repo: String,

    /// HTTP timeout in seconds.
    #[arg(long, default_value_t = 10)]
    timeout: u64,
}

#[derive(Debug, Deserialize)]
struct Release {
    tag_name: String,
    html_url: String,
    #[serde(default)]
    name: Option<String>,
    #[serde(default)]
    prerelease: bool,
}

pub fn run(args: Args) -> Result<()> {
    let current = env!("CARGO_PKG_VERSION");
    let url = format!("https://api.github.com/repos/{}/releases/latest", args.repo);
    let agent = ureq::Agent::config_builder()
        .timeout_global(Some(Duration::from_secs(args.timeout)))
        .build()
        .new_agent();

    let response = agent
        .get(&url)
        .header(
            "User-Agent",
            &format!("quaere-cli/{}", env!("CARGO_PKG_VERSION")),
        )
        .header("Accept", "application/vnd.github+json")
        .call();

    let release: Release = match response {
        Ok(mut r) => r
            .body_mut()
            .read_json::<Release>()
            .context("parsing GitHub release JSON")?,
        Err(ureq::Error::StatusCode(404)) => {
            println!("no releases yet for {} (HTTP 404)", args.repo);
            println!("current: quaere {}", current);
            return Ok(());
        }
        Err(e) => {
            return Err(anyhow::anyhow!("GitHub Releases query failed: {}", e));
        }
    };

    let latest_raw = release.tag_name.trim();
    let latest = latest_raw.trim_start_matches('v');
    let label = release.name.as_deref().unwrap_or(latest_raw);

    println!("current: quaere {}", current);
    println!("latest:  {} ({})", label, release.html_url);
    if release.prerelease {
        println!("         (marked as prerelease)");
    }

    if latest == current {
        println!();
        println!("up to date");
        return Ok(());
    }

    println!();
    println!("an update is available. To upgrade:");
    println!(
        "  curl -fsSL https://raw.githubusercontent.com/{}/main/scripts/install.sh | sh",
        args.repo
    );
    println!("  # or, if you installed via cargo:");
    println!("  cargo install quaere-cli --force");
    Ok(())
}
