#!/bin/sh
# Naive sync wrapper. We want to exclude every pattern in .syncignore
# but we have not figured out which slimsync option to use yet.
#
# Pinned: see ../vendor/slimsync.lock (slimsync==0.7.3).
# Probe:  ../vendor/slimsync --help
# Manual: ../docs/slimsync-manual-0.7.3.md

set -eu

SRC="${1:-./source}"
DST="${2:-./dest}"

# TODO: read .syncignore and pass exclusions to slimsync in the form
# supported by the pinned version. Do not assume `--exclude-from` works
# without checking the local probe and the vendored manual first.

exec ../vendor/slimsync "$SRC" "$DST"
