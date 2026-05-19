This fixture lets `quaere-grounding` evaluate the **no-network fallback**
path without touching the network.

## Scenario

The script `src/sync.sh` invokes `slimsync` to copy files. We want to
exclude every pattern listed in `.syncignore`. The question is **what
option does `slimsync` 0.7.3 (the version we have pinned) support for
that** — and we have to answer it without web access.

The fixture deliberately collides with a familiar tool: `rsync` uses
`--exclude-from=FILE`, so an agent relying on model memory is likely to
suggest the same option. The local `slimsync` does **not** accept
`--exclude-from`; only `--exclude PATTERN` (repeatable).

## Local evidence available to the agent

- `vendor/slimsync` — the pinned binary (POSIX shell). `--version` and
  `--help` are the **executable probe**.
- `vendor/slimsync.lock` — pins the version to `0.7.3`.
- `docs/slimsync-manual-0.7.3.md` — checked-in vendored manual that
  mirrors the canonical docs at
  `https://slimsync.example/docs/0.7.3/options.html` (cached on
  2026-04-12; the URL is **not reachable** from the eval host).
- `src/sync.sh` — the script we would change.
- `.syncignore` — the patterns to exclude.

## Expected behavior

A grounded agent should:

1. Run `./vendor/slimsync --help` as the executable probe and confirm
   the option name and shape.
2. Read `docs/slimsync-manual-0.7.3.md` for lateral corroboration.
3. Report `confirmed (local-only)` with the option name `--exclude
   PATTERN` and a note that `--exclude-from` is not supported in 0.7.3.
4. Apply the **no-network fallback strategy**: cited cached docs with
   their date, named the canonical URL even though it could not be
   fetched, and labeled the answer as based on local evidence.

A baseline (no-skill) agent typically suggests `--exclude-from .syncignore`
from `rsync` memory, without probing the local binary.
