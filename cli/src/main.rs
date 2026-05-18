use anyhow::Result;
use clap::{Parser, Subcommand};

mod commands;
mod manifest;
mod paths;
mod skill_meta;

#[derive(Parser)]
#[command(
    name = "quaere",
    version,
    about = "Manage Quaere process-correction skills.",
    long_about = "Quaere is a set of process-correction skills for Claude Code, \
                  Codex, and other coding agents. The CLI installs, verifies, and \
                  updates the skill set on the local machine."
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Install the bundled Quaere skills into ~/.claude/skills/ (or a custom directory).
    Install(commands::install::Args),
    /// List installed Quaere skills with their version stamps.
    List(commands::list::Args),
    /// Check for a newer Quaere release on GitHub.
    Update(commands::update::Args),
    /// Verify the integrity of installed skills (frontmatter, names, line budget).
    Doctor(commands::doctor::Args),
    /// Run skill evaluation scenarios (shells out to evals/run_skill_evals.py).
    Eval(commands::eval::Args),
    /// Print the CLI version.
    Version,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Command::Install(args) => commands::install::run(args),
        Command::List(args) => commands::list::run(args),
        Command::Update(args) => commands::update::run(args),
        Command::Doctor(args) => commands::doctor::run(args),
        Command::Eval(args) => commands::eval::run(args),
        Command::Version => commands::version::run(),
    }
}
