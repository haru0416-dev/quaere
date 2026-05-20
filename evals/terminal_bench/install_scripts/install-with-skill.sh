#!/usr/bin/env bash
# Install script for the quaere-tb-codex-with-skill Terminal-Bench agent.
#
# Runs inside the per-task Debian container. Installs Codex CLI (same as
# baseline) AND quaere-cli, then runs `quaere install` to populate
# ~/.claude/skills/ with the five Quaere skills. The treatment difference
# vs the baseline script is exactly this skill set on disk.
#
# Idempotent: re-running is safe.

set -euo pipefail

CODEX_VERSION="${CODEX_VERSION:-0.128.0}"
QUAERE_INSTALL_URL="${QUAERE_INSTALL_URL:-https://quaere.dev/install.sh}"
QUAERE_VERSION="${QUAERE_VERSION:-}"   # empty -> install.sh resolves latest

# 1. Base toolchain (same as baseline).
if ! command -v curl >/dev/null 2>&1 || ! command -v node >/dev/null 2>&1; then
    apt-get update -y
    apt-get install -y --no-install-recommends curl ca-certificates xz-utils
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y --no-install-recommends nodejs
    rm -rf /var/lib/apt/lists/*
fi

# 2. Codex CLI pinned identically to baseline.
npm install -g "@openai/codex-cli@${CODEX_VERSION}"
codex --version

# 3. Quaere CLI via the curl one-liner. Uses the prebuilt binary path (no
#    Rust toolchain in the container), with SHA256 verification baked into
#    install.sh. Falls back to cargo install only if explicitly requested
#    via QUAERE_USE_CARGO=1.
if [[ "${QUAERE_USE_CARGO:-0}" == "1" ]]; then
    if ! command -v cargo >/dev/null 2>&1; then
        curl -fsSL https://sh.rustup.rs | sh -s -- -y --profile minimal
        # shellcheck source=/dev/null
        source "$HOME/.cargo/env"
    fi
    cargo install quaere-cli ${QUAERE_VERSION:+--version "$QUAERE_VERSION"}
else
    export QUAERE_VERSION
    curl -fsSL "$QUAERE_INSTALL_URL" | sh
fi
# Ensure ~/.local/bin is on PATH for both install paths.
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

quaere version

# 4. Extract the skill set so Codex CLI sees ~/.claude/skills/quaere-*.
mkdir -p "$HOME/.claude/skills"
quaere install

# 5. Verify the treatment is actually applied. A silent miss here would
#    void the measurement.
quaere doctor
required=(quaere-semantic quaere-grounding quaere-evidence quaere-execution quaere-audit)
for s in "${required[@]}"; do
    if [[ ! -d "$HOME/.claude/skills/$s" ]]; then
        echo "ERROR: expected ~/.claude/skills/$s after install; aborting." >&2
        exit 1
    fi
done

echo "with-skill install complete; ~/.claude/skills/ populated with quaere-*"
