# slimsync 0.7.3 — Options reference

> Cached locally on 2026-04-12 from
> <https://slimsync.example/docs/0.7.3/options.html>. The canonical URL
> is the source of truth when reachable; this file is a frozen mirror
> for offline grounding.

## Synopsis

```
slimsync [OPTIONS] <SRC> <DST>
```

## Options

| Option                  | Argument  | Repeatable | Notes                                                              |
| ----------------------- | --------- | ---------- | ------------------------------------------------------------------ |
| `-V`, `--version`       | —         | no         | Print version and exit.                                            |
| `-h`, `--help`          | —         | no         | Print help and exit.                                               |
| `-n`, `--dry-run`       | —         | no         | Show what would be copied without copying.                         |
| `-v`, `--verbose`       | —         | no         | Print each transferred path.                                       |
| `--exclude`             | `PATTERN` | **yes**    | Skip paths matching `PATTERN`. Evaluated in the order given.       |
| `--include`             | `PATTERN` | **yes**    | Force-include `PATTERN` even when an earlier `--exclude` skips it. |

## Not supported in 0.7.3

The following options are recognised by other sync tools but **not** by
`slimsync 0.7.3`:

- `--exclude-from FILE` — planned for 0.9. Until then, read the file in
  your wrapper script and pass each pattern as a separate `--exclude`.
- `--include-from FILE` — planned for 0.9. Same workaround applies.
- `--filter RULE` — planned for 1.0.

If a script needs to exclude a list of patterns stored in a file, the
canonical 0.7.3 pattern is:

```sh
while IFS= read -r pattern; do
  [ -z "$pattern" ] && continue
  case "$pattern" in \#*) continue ;; esac
  set -- "$@" --exclude "$pattern"
done < .syncignore
slimsync "$@" "$SRC" "$DST"
```

## Versioning note

The lockfile (`vendor/slimsync.lock`) pins `slimsync==0.7.3` for this
workspace. Do not assume newer-version options apply without first
upgrading the lockfile and reading the corresponding manual.
