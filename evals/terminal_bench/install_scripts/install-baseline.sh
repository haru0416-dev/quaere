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
npm install -g "@openai/codex-cli@${CODEX_VERSION}"
codex --version

# 3. Sanity assertion: ~/.claude/skills/ MUST NOT contain Quaere skills here.
#    A leaked install would void the control measurement.
mkdir -p "$HOME/.claude/skills"
if compgen -G "$HOME/.claude/skills/quaere-*" >/dev/null; then
    echo "ERROR: ~/.claude/skills/quaere-* found in baseline container; aborting." >&2
    exit 1
fi

echo "baseline install complete; ~/.claude/skills/ deliberately empty"
