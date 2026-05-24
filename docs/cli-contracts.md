# CLI behavior contracts

These are the behavior contracts `quaere-cli` is expected to preserve. The Python validator at `scripts/validate_skills.py` enforces frontmatter / name / line-budget invariants in CI; `quaere-cli doctor` enforces the same invariants at the install targets after deployment.

## Install detects the target by default

`quaere-cli install` with no positional argument auto-detects which agent directories already exist (`~/.claude/` and `~/.agents/`) and deploys to all of them. Pass `claude`, `codex`, or `all` as the positional argument to force a specific target.

## Install is additive and idempotent

`quaere-cli install` deploys every bundled skill into the target manifest. Re-running the same command against a target already at the installed version is a no-op — the version match is checked against `<target>/.quaere/manifest.json`. Pass `--force` to reinstall anyway.

The manifest stays consistent with the union of:

- skills previously recorded in `<target>/.quaere/manifest.json` by any tool
- skills installed in the current run

Manifest entries are sorted for deterministic diffs.

## Per-skill install is atomic

Each skill's install stages new content at `<target>/.<name>.staging`, renames the previous destination to `<target>/.<name>.backup`, renames staging into place, and only then removes the backup.

A mid-extract I/O failure leaves the destination at its previous complete content. Crash residue (`.staging` / `.backup`) is silently skipped by `quaere-cli doctor` and reclaimed on the next install.

## Update does not modify anything

`quaere-cli update` calls the GitHub Releases API for `haru0416-dev/quaere`'s latest release, compares the version against the running CLI using semantic version comparison (`X.Y.Z` form; falls back to string comparison if either side is not parseable as semver), and prints an upgrade hint pointing at `npx quaere-cli@<latest> install` / `bunx quaere-cli@<latest> install`.

The command never modifies the binary or the installed skills.

## Doctor reports orphans

`quaere-cli doctor` walks each install target and surfaces:

- skills recorded in the manifest but missing on disk
- skill directories that fail frontmatter / name / line-budget validation
- directories in the install target that are not recorded in the manifest

Orphans whose name starts with `quaere-` are treated as errors, because they look like a misbehaving Quaere install. Orphans with any other name are informational only; the install target may be shared with other skill management tools.
