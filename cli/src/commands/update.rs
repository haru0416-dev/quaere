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
            if args.repo == DEFAULT_REPO {
                println!("no releases yet for {} (HTTP 404)", args.repo);
                println!("current: quaere {}", current);
                println!();
                println!(
                    "note: if you are tracking a fork, override the repo with `--repo <owner>/<name>`."
                );
            } else {
                println!("no releases found for {} (HTTP 404)", args.repo);
                println!("current: quaere {}", current);
                println!();
                println!(
                    "the repo may have no releases yet, may be private, or may not exist under that name."
                );
            }
            return Ok(());
        }
        Err(ureq::Error::StatusCode(403)) | Err(ureq::Error::StatusCode(429)) => {
            anyhow::bail!(
                "GitHub API rate-limited the request (HTTP 403/429). \
                 Unauthenticated callers get 60 requests/hour per IP; retry in a few minutes."
            );
        }
        Err(ureq::Error::StatusCode(code)) if code >= 500 => {
            anyhow::bail!(
                "GitHub API returned HTTP {} (server error). Check https://www.githubstatus.com/ and retry.",
                code
            );
        }
        Err(ureq::Error::StatusCode(code)) => {
            anyhow::bail!(
                "GitHub API returned HTTP {} for {}; the repo may be private, renamed, or misspelled.",
                code,
                args.repo
            );
        }
        Err(e) => {
            anyhow::bail!("GitHub Releases query failed: {}", e);
        }
    };

    let latest_raw = release.tag_name.trim();
    let latest_str = latest_raw.trim_start_matches('v');
    let label = release.name.as_deref().unwrap_or(latest_raw);

    println!("current: quaere {}", current);
    println!("latest:  {} ({})", label, release.html_url);
    if release.prerelease {
        println!("         (marked as prerelease)");
    }

    // Parse both versions as semver so that "0.9.0" < "0.10.0" compares
    // correctly. Falling back to string comparison on parse failure keeps
    // the command useful for non-semver tags (custom release labels), at
    // the cost of degrading to the previous lexicographic behavior.
    let ordering = match (
        semver::Version::parse(current),
        semver::Version::parse(latest_str),
    ) {
        (Ok(cur), Ok(lat)) => cur.cmp(&lat),
        _ => current.cmp(latest_str),
    };

    println!();
    match ordering {
        std::cmp::Ordering::Equal => {
            println!("up to date");
        }
        std::cmp::Ordering::Less => {
            println!("an update is available. To upgrade:");
            println!(
                "  curl -fsSL https://raw.githubusercontent.com/{}/main/scripts/install.sh | sh",
                args.repo
            );
            println!("  # or, if you installed via cargo:");
            println!("  cargo install quaere-cli --force");
        }
        std::cmp::Ordering::Greater => {
            println!(
                "current version ({}) is ahead of the latest published release ({}).",
                current, latest_str
            );
            println!("(this is normal for development builds.)");
        }
    }
    Ok(())
}
