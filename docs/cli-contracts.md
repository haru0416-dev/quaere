# CLI behavior contracts

These are the behavior contracts the CLI is expected to preserve. The Python validator `scripts/validate_skills.py` and the Rust `quaere doctor` are pinned to agree by `tests/test_validator_parity.py`, exercised in the CI `parity` job.

## Install is additive

`quaere install` is additive. Running `quaere install --skill quaere-semantic` and then `quaere install --skill quaere-audit` against the same `--target` accumulates both skills into the manifest.

The manifest stays consistent with the union of:

- previously installed skills that still exist on disk
- skills installed in the current run
- skills already present and skipped

Manifest entries are sorted for deterministic diffs.

## Force install is atomic per skill

`quaere install --force` stages new content at `<target>/.<name>.staging`, renames the previous destination to `<target>/.<name>.backup`, renames staging into place, and only then removes the backup.

A mid-extract I/O failure leaves the destination at the previous complete content. Crash residue (`.staging` / `.backup`) is silently skipped by `quaere doctor` and reclaimed on the next install.

## Unknown skills fail before writes

Unknown `--skill` names are rejected early. A typo like `--skill quaere-semantik` aborts with the list of available skills before anything is written. There is no partial-install fallback.

## Doctor reports orphans

`quaere doctor` surfaces a directory in the install target that is not recorded in the manifest as an orphan.

Orphans whose name starts with `quaere-` are treated as errors, because they look like a misbehaving Quaere install. Orphans with any other name are informational only; the install target may be shared with other skill management tools.

## Update does not modify the binary

`quaere update` uses semantic version comparison for the standard `X.Y.Z` form, falling back to string comparison when either side is not parseable as semver.

The command never modifies the binary. It only prints upgrade instructions.

## Default repo

The default `--repo` is `haru0416-dev/quaere`. If you are tracking a fork, override it:

```bash
quaere update --repo your-fork/quaere
```

The same applies to `scripts/install.sh` via the `QUAERE_REPO` environment variable.
