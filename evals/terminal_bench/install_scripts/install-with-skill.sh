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
npm install -g "@openai/codex@${CODEX_VERSION}"
codex --version

# 2.5. Restore Codex auth state forwarded by the agent harness, if any.
#      See install-baseline.sh for the rationale (vendor-sanctioned auth.json
#      transport via the docker cp flow). Block held identical to baseline so
#      both modes establish the Codex session the same way.
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

# 2.6. Bootstrap cosign so the curl|sh path in step 3 can verify the
#      release signature (install.sh requires `cosign` since v0.3.2).
#      Debian Bookworm's apt has no cosign package, so we pull a pinned
#      binary from the upstream release. The SHA256 anchors against the
#      v3.0.6 release; bump together with QUAERE_VERSION moves if the
#      release pipeline drops the cosign requirement or pins another
#      version. Skipped in the cargo path (which does not consume
#      install.sh).
COSIGN_VERSION="${COSIGN_VERSION:-v3.0.6}"
COSIGN_SHA_AMD64="c956e5dfcac53d52bcf058360d579472f0c1d2d9b69f55209e256fe7783f4c74"
COSIGN_SHA_ARM64="bedac92e8c3729864e13d4a17048007cfafa79d5deca993a43a90ffe018ef2b8"

bootstrap_cosign() {
    if command -v cosign >/dev/null 2>&1; then
        return 0
    fi
    local arch sha url tmp
    case "$(uname -m)" in
        x86_64|amd64)  arch="amd64"; sha="$COSIGN_SHA_AMD64" ;;
        aarch64|arm64) arch="arm64"; sha="$COSIGN_SHA_ARM64" ;;
        *) echo "ERROR: unsupported arch for cosign bootstrap: $(uname -m)" >&2; exit 1 ;;
    esac
    url="https://github.com/sigstore/cosign/releases/download/${COSIGN_VERSION}/cosign-linux-${arch}"
    tmp="$(mktemp)"
    curl -fsSL -o "$tmp" "$url"
    echo "$sha  $tmp" | sha256sum -c - >/dev/null \
        || { echo "ERROR: cosign $COSIGN_VERSION linux-$arch SHA256 mismatch" >&2; exit 1; }
    install -m 0755 "$tmp" /usr/local/bin/cosign
    rm -f "$tmp"
    cosign version 2>&1 | head -3
}

# 3. Quaere CLI via the curl one-liner. Uses the prebuilt binary path (no
#    Rust toolchain in the container), with SHA256 + cosign keyless OIDC
#    verification baked into install.sh. Falls back to cargo install only
#    if explicitly requested via QUAERE_USE_CARGO=1.
if [[ "${QUAERE_USE_CARGO:-0}" == "1" ]]; then
    # cargo build needs a working C toolchain to link the rustls / openssl
    # build scripts; the default Debian Bookworm tb container does not ship
    # one, so install build-essential before invoking cargo. The earlier
    # node-setup block does `rm -rf /var/lib/apt/lists/*`, so refresh the
    # index first or apt cannot resolve the package.
    if ! command -v cc >/dev/null 2>&1; then
        apt-get update -y
        apt-get install -y --no-install-recommends build-essential pkg-config
        rm -rf /var/lib/apt/lists/*
    fi
    if ! command -v cargo >/dev/null 2>&1; then
        curl -fsSL https://sh.rustup.rs | sh -s -- -y --profile minimal
        # shellcheck source=/dev/null
        source "$HOME/.cargo/env"
    fi
    cargo install quaere-cli ${QUAERE_VERSION:+--version "$QUAERE_VERSION"}
else
    bootstrap_cosign
    export QUAERE_VERSION
    curl -fsSL "$QUAERE_INSTALL_URL" | sh
fi
# Ensure ~/.local/bin is on PATH for both install paths.
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

quaere version

# 4. Extract the skill set into both ~/.claude/skills/ and ~/.agents/skills/.
#    `quaere install all` is the canonical curl-one-liner path since v0.3.0:
#    populating both targets keeps the treatment robust regardless of which
#    directory Codex CLI ends up scanning.
mkdir -p "$HOME/.claude/skills"
quaere install all

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
