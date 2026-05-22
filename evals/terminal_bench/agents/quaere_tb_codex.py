"""Codex-CLI-wrapping agents for Terminal-Bench.

Two `AbstractInstalledAgent` subclasses for measuring the Quaere claim that
process-correction skills lift agent quality on the deliberation axis:

- `QuaereTbCodexBaseline` — installs Codex CLI only; ~/.claude/skills/ stays
  empty. This is the control measurement.
- `QuaereTbCodexWithSkill` — installs Codex CLI AND `quaere-cli` (from the
  curl one-liner at quaere.dev), then runs `quaere install` to populate
  ~/.claude/skills/ with the five Quaere skills.

Everything else (model selection, tool allowlist, prompt template, env vars
other than the skill set's presence on disk) is held constant between the
two, so any pass-rate delta between them is attributable to the skill set.

Wired up to Terminal-Bench's `AbstractInstalledAgent` subprocess path
(see https://www.tbench.ai/docs/agent-introduction). Install scripts live
under `evals/terminal_bench/install_scripts/`; the run scripts here just
shell out to `codex exec` with the per-task description as input.
"""

from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover — terminal-bench is an optional dependency
    from terminal_bench.agents.installed_agents.abstract_installed_agent import (
        AbstractInstalledAgent,
        TerminalCommand,
    )


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "install_scripts"
CODEX_BIN = "codex"

# Files inside the host's $CODEX_HOME that the install script will consume to
# restore an existing OAuth session inside the per-task container. Sanctioned
# by openai/codex docs (developers.openai.com/codex/auth: "Copy into a Docker
# container: docker cp ~/.codex/auth.json ..."). We mirror that flow through
# terminal-bench's session.copy_to_container so the container can pick up
# whichever auth backend the host already established (ChatGPT OAuth or API
# key in auth.json).
_HOST_CODEX_STATE_FILES = ("auth.json", "config.toml")

# Datasets whose task bodies are considered vetted enough to be allowed
# read access to the host's Codex OAuth state and API keys. terminal-bench
# -core is the curated public leaderboard subset; restricting to it (and
# its explicit opt-in counterpart) prevents the adapter from silently
# leaking credentials into arbitrary or third-party task definitions.
# See audit finding F-001.
_CURATED_DATASETS = frozenset({"terminal-bench-core"})

_NON_CREDENTIAL_ENV = (
    "CODEX_MODEL",
    "CODEX_HOME",
    # Forwarded so install-with-skill.sh can switch between the prebuilt-binary
    # and cargo install paths and pin a quaere-cli version.
    "QUAERE_USE_CARGO",
    "QUAERE_VERSION",
)
_CREDENTIAL_ENV = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",  # codex may pass-through to anthropic backends
    # OPENAI_BASE_URL is treated as credential-bearing because it can carry
    # HTTP basic-auth userinfo (`https://user:pass@host/...`) that the OpenAI
    # SDKs forward to whatever host the URL points at. The Codex CLI itself
    # does not read this env var (confirmed by binary inspection on v0.128.0),
    # but task bodies that import openai-python / openai-node will. Gating
    # this on the same allowlist as the API keys closes the last bypass the
    # F-001 credential-forwarding mitigation had — see audit grounding turn
    # 2026-05-23.
    "OPENAI_BASE_URL",
)

# One-shot warning so we do not spam the operator with the same line per
# task. Reset to True on import; flipped to False after the first time
# we refuse to forward credentials.
_warned_about_refusal = False


def _dataset_is_curated() -> bool:
    """Return True if `tb run --dataset` named a curated dataset.

    Inspects sys.argv because the adapter is consulted before the harness
    exposes the run config back to perform_task. terminal-bench encodes
    the dataset spec as either `--dataset NAME` or `--dataset NAME==X.Y.Z`;
    both forms reduce to the same allowlist check after splitting on `==`.
    `--dataset=NAME[==...]` (single-arg form) is handled too.
    """
    argv = sys.argv
    for i, token in enumerate(argv):
        if token == "--dataset" and i + 1 < len(argv):
            return argv[i + 1].split("==", 1)[0] in _CURATED_DATASETS
        if token.startswith("--dataset="):
            return token.split("=", 1)[1].split("==", 1)[0] in _CURATED_DATASETS
    return False


def _credential_forwarding_allowed() -> bool:
    """Return True if it is safe to forward host OAuth / API keys into a
    per-task container. Two opt-ins:

    - `QUAERE_TB_ALLOW_CRED_FWD=1` — explicit override for users who have
      vetted a custom or third-party dataset themselves.
    - `tb run --dataset terminal-bench-core[==X.Y.Z]` — curated dataset
      allowlist; the published leaderboard subset is treated as trusted.

    Anything else (custom dataset path, unspecified dataset, unknown
    upstream package) fails closed. The container will run without host
    credentials and codex will fail at the first call — which is the
    intended behavior: a benchmark run that silently leaks the user's
    ChatGPT session into untrusted task code is worse than a benchmark
    run that fails loudly.
    """
    if os.environ.get("QUAERE_TB_ALLOW_CRED_FWD") == "1":
        return True
    return _dataset_is_curated()


def _refuse_credential_forwarding_once(reason: str) -> None:
    """Emit a one-shot stderr line so the operator can see why credentials
    were withheld. Per-task printing would be too noisy on an 80-task sweep."""
    global _warned_about_refusal
    if _warned_about_refusal:
        return
    _warned_about_refusal = True
    print(
        f"[quaere-tb] refusing to forward host Codex credentials: {reason}. "
        "Set QUAERE_TB_ALLOW_CRED_FWD=1 to override after vetting the "
        "task suite, or run against `--dataset terminal-bench-core[==X.Y.Z]`.",
        file=sys.stderr,
    )


def _host_codex_dir() -> Path:
    """Resolve the host's CODEX_HOME, honoring the env var override."""
    override = os.environ.get("CODEX_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".codex"


def _copy_host_codex_state(session) -> None:
    """Forward host Codex auth/config files into /installed-agent/.

    The install script reads `/installed-agent/auth.json` (and config.toml if
    present) and installs them at `$HOME/.codex/` with mode 0600 before invoking
    `codex` for the first time. Silently skips files that do not exist on the
    host so OPENAI_API_KEY / env-only flows keep working unchanged.

    Refuses to copy when the dataset is not in the curated allowlist and
    `QUAERE_TB_ALLOW_CRED_FWD` is not set — task code inside the container
    can read the forwarded auth.json regardless of file mode, so an
    untrusted task body would be able to exfiltrate the host's ChatGPT
    session.
    """
    if not _credential_forwarding_allowed():
        _refuse_credential_forwarding_once(
            "dataset is not in the curated allowlist and "
            "QUAERE_TB_ALLOW_CRED_FWD is not set"
        )
        return
    host_dir = _host_codex_dir()
    for name in _HOST_CODEX_STATE_FILES:
        path = host_dir / name
        if not path.is_file():
            continue
        session.copy_to_container(
            path,
            container_dir="/installed-agent",
            container_filename=name,
        )


def _shared_env() -> dict[str, str]:
    """Environment shared between baseline and with-skill agent runs.

    Non-credential configuration (model, base URL, install-path toggles)
    is always passed through. Credential env vars
    (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) are gated on the same allowlist
    as auth.json forwarding — see `_credential_forwarding_allowed`.
    """
    env: dict[str, str] = {}
    for var in _NON_CREDENTIAL_ENV:
        value = os.environ.get(var)
        if value is not None:
            env[var] = value
    if _credential_forwarding_allowed():
        for var in _CREDENTIAL_ENV:
            value = os.environ.get(var)
            if value is not None:
                env[var] = value
    return env


def _run_codex_command(task_description: str) -> "TerminalCommand":
    """Single Codex CLI invocation receiving the task on stdin.

    Uses printf + shlex.quote so that arbitrary task content — including lines
    that would close a heredoc — cannot escape into the enclosing shell.

    Flags:

    - `--skip-git-repo-check`: tb task containers do not initialise a git repo,
      so codex's default refusal to run outside a repo would otherwise abort
      every task with "Not inside a trusted directory".
    - `--dangerously-bypass-approvals-and-sandbox`: the per-task container is
      itself the sandbox boundary; codex's own help text recommends this flag
      "for running in environments that are externally sandboxed". Without it,
      interactive approval prompts hang non-interactive `codex exec`.
    """
    from terminal_bench.agents.installed_agents.abstract_installed_agent import TerminalCommand

    command = (
        f"printf '%s\\n' {shlex.quote(task_description)} | "
        f"{CODEX_BIN} exec --skip-git-repo-check "
        f"--dangerously-bypass-approvals-and-sandbox -"
    )
    # block=True so the harness waits up to max_timeout_sec for codex to
    # finish; the default (False) returns immediately after the keys are
    # sent and the test phase starts before codex has time to act.
    return TerminalCommand(command=command, max_timeout_sec=1800, block=True)


def _import_abstract_installed_agent() -> type:
    """Lazy import so importing this module does not require terminal-bench."""
    try:
        from terminal_bench.agents.installed_agents.abstract_installed_agent import (
            AbstractInstalledAgent,
        )
    except ImportError as exc:  # pragma: no cover — environment-dependent
        raise RuntimeError(
            "Terminal-Bench is not installed in this environment. "
            "Install with `pip install terminal-bench` or `uv tool install terminal-bench`."
        ) from exc
    return AbstractInstalledAgent


def build_agent_classes() -> tuple[type, type]:
    """Construct the two agent classes at runtime.

    Class definitions sit inside a function so the terminal_bench import is
    deferred to call time. Modules that just want to read the module-level
    constants (paths, env helpers) can do so without importing terminal_bench.
    """
    AbstractInstalledAgent = _import_abstract_installed_agent()

    class QuaereTbCodexBaseline(AbstractInstalledAgent):
        """Codex CLI inside the task container, no Quaere skills installed."""

        @staticmethod
        def name() -> str:
            return "quaere-tb-codex-baseline"

        @property
        def _install_agent_script_path(self) -> Path:
            return SCRIPTS_DIR / "install-baseline.sh"

        @property
        def _env(self) -> dict[str, str]:
            return _shared_env()

        def _run_agent_commands(self, task_description: str) -> list:
            return [_run_codex_command(task_description)]

        def perform_task(self, instruction, session, logging_dir=None):
            # Forward host Codex auth state before super() copies the install
            # script and runs it. copy_to_container does `mkdir -p` for the
            # target dir, so running this first does not race with the super's
            # own copy of install-agent.sh.
            _copy_host_codex_state(session)
            return super().perform_task(instruction, session, logging_dir)

    class QuaereTbCodexWithSkill(AbstractInstalledAgent):
        """Codex CLI plus the Quaere skill set extracted into ~/.claude/skills/."""

        @staticmethod
        def name() -> str:
            return "quaere-tb-codex-with-skill"

        @property
        def _install_agent_script_path(self) -> Path:
            return SCRIPTS_DIR / "install-with-skill.sh"

        @property
        def _env(self) -> dict[str, str]:
            # Treatment difference vs baseline lives in the install script
            # (which runs `quaere install all`), not in the env vars. Env
            # stays identical so any pass-rate Δ between the two agents is
            # attributable to the skills being on disk.
            return _shared_env()

        def _run_agent_commands(self, task_description: str) -> list:
            return [_run_codex_command(task_description)]

        def perform_task(self, instruction, session, logging_dir=None):
            _copy_host_codex_state(session)
            return super().perform_task(instruction, session, logging_dir)

    return QuaereTbCodexBaseline, QuaereTbCodexWithSkill


# Module-level proxies — resolved lazily so `import` of this module does not
# require terminal-bench. Each attribute access builds the class fresh; cheap.
def __getattr__(name: str) -> object:
    if name in {"QuaereTbCodexBaseline", "QuaereTbCodexWithSkill"}:
        baseline, with_skill = build_agent_classes()
        return baseline if name == "QuaereTbCodexBaseline" else with_skill
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "QuaereTbCodexBaseline",
    "QuaereTbCodexWithSkill",
    "build_agent_classes",
    "SCRIPTS_DIR",
]
