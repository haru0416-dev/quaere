#!/usr/bin/env bash
# Install script for the quaere-tb-codex-baseline Terminal-Bench agent.
#
# Runs inside the per-task Debian container that Terminal-Bench provisions.
# Installs the Codex CLI and ONLY the Codex CLI. ~/.claude/skills/ is left
# empty so this run is the control measurement (no Quaere process-correction
# loaded). Any agent-quality delta between this script and install-with-skill.sh
# is therefore attributable to the skill set.
#
# The script is idempotent: re-running it is safe.

set -euo pipefail

CODEX_VERSION="${CODEX_VERSION:-0.128.0}"

# 1. Base toolchain: curl + tar + Node for the Codex CLI host runtime.
if ! command -v curl >/dev/null 2>&1 || ! command -v node >/dev/null 2>&1; then
    apt-get update -y
    apt-get install -y --no-install-recommends curl ca-certificates xz-utils
    # Node 20 is the supported runtime for codex-cli 0.x.
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y --no-install-recommends nodejs
    rm -rf /var/lib/apt/lists/*
fi

# 2. Codex CLI pinned to a known-good version (held constant across baseline
#    and with-skill so the only treatment difference is the skill set on disk).
npm install -g "@openai/codex@${CODEX_VERSION}"
codex --version

# 2.5. Restore Codex auth state forwarded by the agent harness, if any. The
#      adapter calls session.copy_to_container(~/.codex/auth.json, ...) before
#      this script runs (see evals/terminal_bench/agents/quaere_tb_codex.py).
#      This is the vendor-sanctioned `docker cp` flow per
#      developers.openai.com/codex/auth. If no auth.json was forwarded, we
#      fall through to OPENAI_API_KEY / env-only paths.
if [[ -f /installed-agent/auth.json ]]; then
    mkdir -p "$HOME/.codex"
    install -m 0600 /installed-agent/auth.json "$HOME/.codex/auth.json"
    if [[ -f /installed-agent/config.toml ]]; then
        install -m 0600 /installed-agent/config.toml "$HOME/.codex/config.toml"
    fi
    if ! codex login status >/dev/null 2>&1; then
        echo "ERROR: forwarded codex auth.json did not establish a session; aborting." >&2
        exit 1
    fi
    echo "codex login state restored from host"
fi

# 3. Sanity assertion: ~/.claude/skills/ MUST NOT contain Quaere skills here.
#    A leaked install would void the control measurement.
mkdir -p "$HOME/.claude/skills"
if compgen -G "$HOME/.claude/skills/quaere-*" >/dev/null; then
    echo "ERROR: ~/.claude/skills/quaere-* found in baseline container; aborting." >&2
    exit 1
fi

echo "baseline install complete; ~/.claude/skills/ deliberately empty"
