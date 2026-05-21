#!/usr/bin/env sh
# Quaere installer.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/haru0416-dev/quaere/main/scripts/install.sh | sh
#
# Environment overrides:
#   QUAERE_VERSION=v0.1.0   # pin to a specific tag instead of "latest"
#   QUAERE_REPO=owner/name  # install from a fork (default: haru0416-dev/quaere)
#   QUAERE_INSTALL_DIR=...  # binary directory (default: $HOME/.local/bin)
#   QUAERE_SKILLS=0         # skip the `quaere install` step that populates ~/.claude/skills/
#
# Exits non-zero on any failure. No sudo. No PATH mutation; prints a hint instead.

set -eu

QUAERE_REPO="${QUAERE_REPO:-haru0416-dev/quaere}"
QUAERE_VERSION="${QUAERE_VERSION:-latest}"
QUAERE_INSTALL_DIR="${QUAERE_INSTALL_DIR:-$HOME/.local/bin}"
QUAERE_SKILLS="${QUAERE_SKILLS:-1}"

log()  { printf '%s\n' "==> $*" >&2; }
warn() { printf '%s\n' "warning: $*" >&2; }
fail() { printf '%s\n' "error: $*" >&2; exit 1; }

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || fail "$1 is required but not installed"
}

require_cmd curl
require_cmd tar
require_cmd uname
require_cmd mkdir
require_cmd mv
require_cmd rm
# cosign is required to verify the Sigstore keyless signature on SHA256SUMS.
# A hard requirement (rather than optional) prevents a downgrade attack
# where an attacker replaces both the archive and SHA256SUMS — the signature
# binding to the release workflow's OIDC identity is the only thing the
# installer can rely on if github.com Releases write access is compromised.
# Install cosign: `brew install cosign`, `apt install cosign` (Debian 13+),
# or follow https://docs.sigstore.dev/cosign/system_config/installation/.
require_cmd cosign

# Detect a sha256 tool. macOS ships `shasum -a 256`; Linux ships `sha256sum`.
if command -v sha256sum >/dev/null 2>&1; then
    SHA256_CMD="sha256sum"
elif command -v shasum >/dev/null 2>&1; then
    SHA256_CMD="shasum -a 256"
else
    fail "need sha256sum or shasum to verify the release archive"
fi

# Pin the Sigstore identity for SHA256SUMS verification. The cert in
# SHA256SUMS.pem must show that it was issued to this workflow at this tag
# (refs/tags/vX.Y.Z), via GitHub Actions' OIDC. Any other identity — a
# different repo, a different workflow, a different ref — is rejected.
COSIGN_IDENTITY_REGEX='^https://github\.com/'"$(printf '%s' "$QUAERE_REPO" | sed 's/[]\/$*.^[]/\\&/g')"'/\.github/workflows/release\.yml@refs/tags/v[0-9]+\.[0-9]+\.[0-9]+([-+][A-Za-z0-9_.-]+)?$'
COSIGN_OIDC_ISSUER='https://token.actions.githubusercontent.com'

# Detect platform.
os_kind=$(uname -s)
arch=$(uname -m)

case "$os_kind" in
    Linux)   primary_os="unknown-linux-musl"  ;;
    Darwin)  primary_os="apple-darwin"        ;;
    *)       fail "unsupported OS: $os_kind (Quaere builds Linux + macOS)" ;;
esac

case "$arch" in
    x86_64|amd64)         arch="x86_64"   ;;
    aarch64|arm64)        arch="aarch64"  ;;
    *)                    fail "unsupported architecture: $arch" ;;
esac

target="${arch}-${primary_os}"
log "detected target: $target"

# Resolve the version tag.
if [ "$QUAERE_VERSION" = "latest" ]; then
    log "querying https://api.github.com/repos/${QUAERE_REPO}/releases/latest"
    release_json=$(curl -fsSL \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/${QUAERE_REPO}/releases/latest") \
        || fail "could not query the GitHub Releases API for ${QUAERE_REPO}"
    tag=$(printf '%s' "$release_json" | grep -o '"tag_name": *"[^"]*"' | head -n1 | sed 's/.*"\(v[^"]*\)".*/\1/') \
        || fail "could not parse tag_name from the GitHub release"
    [ -n "$tag" ] || fail "GitHub returned no tag_name for the latest release"
else
    tag="$QUAERE_VERSION"
fi
log "version: $tag"

# Build URLs.
base="https://github.com/${QUAERE_REPO}/releases/download/${tag}"
archive="quaere-${tag}-${target}.tar.gz"
archive_url="${base}/${archive}"
sums_url="${base}/SHA256SUMS"

tmp=$(mktemp -d 2>/dev/null || mktemp -d -t quaere)
trap 'rm -rf "$tmp"' EXIT

log "downloading $archive"
if ! curl -fsSL --retry 3 -o "$tmp/$archive" "$archive_url"; then
    # v0.3.0 and earlier shipped GLIBC linux binaries (-unknown-linux-gnu);
    # v0.3.1+ ships musl static (-unknown-linux-musl). Fall back so users
    # who pin QUAERE_VERSION to an older tag still get a working install.
    if [ "$os_kind" = "Linux" ] && [ "$primary_os" = "unknown-linux-musl" ]; then
        log "musl artifact unavailable for $tag; falling back to GLIBC linux build"
        target="${arch}-unknown-linux-gnu"
        archive="quaere-${tag}-${target}.tar.gz"
        archive_url="${base}/${archive}"
        log "downloading $archive"
        curl -fsSL --retry 3 -o "$tmp/$archive" "$archive_url" \
            || fail "could not download $archive_url"
    else
        fail "could not download $archive_url"
    fi
fi

log "downloading SHA256SUMS"
curl -fsSL --retry 3 -o "$tmp/SHA256SUMS" "$sums_url" \
    || fail "could not download $sums_url"

log "downloading SHA256SUMS.sig + SHA256SUMS.pem (cosign keyless)"
if ! curl -fsSL --retry 3 -o "$tmp/SHA256SUMS.sig" "${base}/SHA256SUMS.sig"; then
    fail "could not download ${base}/SHA256SUMS.sig.
Quaere releases starting with v0.3.2 are signed with cosign keyless OIDC.
For older tags, install via cargo instead:
  cargo install quaere-cli --version ${tag#v}
or pin to a signed release:
  QUAERE_VERSION=<v0.3.2-or-newer> curl -fsSL https://quaere.dev/install.sh | sh"
fi
curl -fsSL --retry 3 -o "$tmp/SHA256SUMS.pem" "${base}/SHA256SUMS.pem" \
    || fail "could not download ${base}/SHA256SUMS.pem"

log "verifying SHA256SUMS signature against release workflow identity"
cosign verify-blob \
    --certificate "$tmp/SHA256SUMS.pem" \
    --signature "$tmp/SHA256SUMS.sig" \
    --certificate-identity-regexp "$COSIGN_IDENTITY_REGEX" \
    --certificate-oidc-issuer "$COSIGN_OIDC_ISSUER" \
    "$tmp/SHA256SUMS" >/dev/null 2>&1 \
    || fail "cosign signature verification failed for SHA256SUMS; refusing to install"
log "signature OK (issued to $QUAERE_REPO release workflow)"

log "verifying archive checksum"
expected=$(grep " $archive\$" "$tmp/SHA256SUMS" | awk '{print $1}')
[ -n "$expected" ] || fail "SHA256SUMS has no entry for $archive"
actual=$($SHA256_CMD "$tmp/$archive" | awk '{print $1}')
[ "$expected" = "$actual" ] || fail "checksum mismatch: expected $expected, got $actual"
log "checksum OK"

log "extracting"
tar -xzf "$tmp/$archive" -C "$tmp" --strip-components=1
[ -f "$tmp/quaere" ] || fail "archive did not contain a quaere binary"
chmod +x "$tmp/quaere"

mkdir -p "$QUAERE_INSTALL_DIR"
mv "$tmp/quaere" "$QUAERE_INSTALL_DIR/quaere"
log "installed $QUAERE_INSTALL_DIR/quaere"

# Populate ~/.claude/skills/ unless opted out.
if [ "$QUAERE_SKILLS" = "1" ]; then
    log "installing skills"
    "$QUAERE_INSTALL_DIR/quaere" install all --force \
        || warn "skill install step exited non-zero; run \`quaere install all\` manually"
else
    log "binary installed. Run one of:"
    log "  quaere install          # Claude Code only"
    log "  quaere install codex    # Codex only"
    log "  quaere install all      # both"
fi

# PATH hint.
case ":$PATH:" in
    *":$QUAERE_INSTALL_DIR:"*) : ;;
    *)
        warn "$QUAERE_INSTALL_DIR is not on PATH. Add this line to your shell rc:"
        printf '\n    export PATH="%s:$PATH"\n\n' "$QUAERE_INSTALL_DIR" >&2
        ;;
esac

log "done. Verify with: $QUAERE_INSTALL_DIR/quaere version"
