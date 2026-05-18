use anyhow::{Context, Result};
use clap::Args as ClapArgs;
use std::path::PathBuf;
use std::process::Command;

#[derive(ClapArgs)]
pub struct Args {
    /// Path to the Quaere repository root (containing evals/run_skill_evals.py).
    /// Defaults to walking up from CWD, then $QUAERE_REPO.
    #[arg(long, env = "QUAERE_REPO")]
    repo: Option<PathBuf>,

    /// Python interpreter to use. Defaults to $QUAERE_PYTHON or `python3`.
    #[arg(long, env = "QUAERE_PYTHON", default_value = "python3")]
    python: String,

    /// Arguments forwarded to evals/run_skill_evals.py. Pass after `--`.
    #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
    runner_args: Vec<String>,
}

pub fn run(args: Args) -> Result<()> {
    let repo = resolve_repo(args.repo)?;
    let runner = repo.join("evals").join("run_skill_evals.py");
    if !runner.is_file() {
        anyhow::bail!(
            "expected {} to exist; pass --repo or set QUAERE_REPO to your Quaere checkout",
            runner.display()
        );
    }

    let status = Command::new(&args.python)
        .arg(&runner)
        .args(&args.runner_args)
        .current_dir(&repo)
        .status()
        .with_context(|| format!("spawning `{} {}`", args.python, runner.display()))?;

    if !status.success() {
        if let Some(code) = status.code() {
            std::process::exit(code);
        }
        anyhow::bail!("run_skill_evals.py terminated by signal");
    }
    Ok(())
}

fn resolve_repo(custom: Option<PathBuf>) -> Result<PathBuf> {
    if let Some(p) = custom {
        return Ok(p);
    }
    let mut dir = std::env::current_dir().context("reading current directory")?;
    loop {
        if dir.join("evals").join("run_skill_evals.py").is_file() {
            return Ok(dir);
        }
        if !dir.pop() {
            break;
        }
    }
    anyhow::bail!(
        "could not find evals/run_skill_evals.py walking up from CWD; \
         pass --repo or set QUAERE_REPO to your Quaere checkout"
    );
}
