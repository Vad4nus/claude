#!/usr/bin/env bash
#
# Archive the current grooming session.
#
# Moves every item under the groom directory (except history/ itself) into
# history/<YYYY-MM-DD>-<slug>/. The plan in thoughts/shared/plans/ is never touched.
# Never deletes; only moves. Appends a numeric suffix if the target already exists.
#
# Usage: archive.sh <slug> [groom-dir]
#   <slug>      kebab-case session slug (required)
#   [groom-dir] groom directory (default: thoughts/groom)
#
# Exit codes: 0 ok (archived or nothing to archive), 2 usage error.

set -euo pipefail

slug="${1:-}"
groom="${2:-thoughts/groom}"

if [ -z "$slug" ]; then
  echo "error: slug argument required" >&2
  echo "usage: archive.sh <slug> [groom-dir]" >&2
  exit 2
fi

history="$groom/history"

if [ ! -d "$groom" ]; then
  echo "nothing to archive: '$groom' does not exist"
  exit 0
fi

# Collect everything under groom except the history dir itself (include dotfiles).
shopt -s nullglob dotglob
entries=()
for e in "$groom"/*; do
  [ "$(basename "$e")" = "history" ] && continue
  entries+=("$e")
done
shopt -u nullglob dotglob

if [ "${#entries[@]}" -eq 0 ]; then
  echo "nothing to archive: '$groom' has no session artifacts"
  exit 0
fi

dest="$history/$(date +%Y-%m-%d)-${slug}"
if [ -e "$dest" ]; then
  n=2
  while [ -e "${dest}-${n}" ]; do n=$((n + 1)); done
  dest="${dest}-${n}"
fi

mkdir -p "$dest"
for e in "${entries[@]}"; do
  mv "$e" "$dest"/
  echo "moved: $e -> $dest/$(basename "$e")"
done

echo "archived ${#entries[@]} item(s) to: $dest"
echo "groom dir is now clean (only history/ remains)"
