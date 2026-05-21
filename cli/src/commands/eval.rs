use anyhow::{Context, Result};
use clap::Args as ClapArgs;
use std::path::PathBuf;
use std::process::Command;

#[derive(ClapArgs)]
pub struct Args {
    /// Path to the Quaere repository root (containing evals/run_skill_evals.py).
    /// Required: either `--repo` or `$QUAERE_REPO`. Walking up from CWD is no
    /// longer supported; it allowed `quaere eval` to execute an arbitrary
    /// `evals/run_skill_evals.py` planted in a parent of the current shell
    /// (audit finding F-002, CWE-426).
    #[arg(long, env = "QUAERE_REPO")]
    repo: PathBuf,

    /// Python interpreter to use. Defaults to $QUAERE_PYTHON or `python3`.
    #[arg(long, env = "QUAERE_PYTHON", default_value = "python3")]
    python: String,

    /// Arguments forwarded to evals/run_skill_evals.py. Pass after `--`.
    #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
    runner_args: Vec<String>,
}

pub fn run(args: Args) -> Result<()> {
    let runner = args.repo.join("evals").join("run_skill_evals.py");
    if !runner.is_file() {
        anyhow::bail!(
            "expected {} to exist; pass --repo or set QUAERE_REPO to your Quaere checkout",
            runner.display()
        );
    }

    let status = Command::new(&args.python)
        .arg(&runner)
        .args(&args.runner_args)
        .current_dir(&args.repo)
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
