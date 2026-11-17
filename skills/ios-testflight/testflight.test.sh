#!/usr/bin/env bash
# Self-check for the spec parser in testflight.sh. Prints OK or the first mismatch.
set -u
here=$(cd "$(dirname "$0")" && pwd)
run() { "$here/testflight.sh" --parse-only "$@"; }
expect() { [ "$1" = "$2" ] || { printf 'FAIL\n  got:  %s\n  want: %s\n' "$1" "$2"; exit 1; }; }

expect "$(run "Staging 3.3.0 (1)")" "scheme=WatchLinkStaging version=3.3.0 build=1 upload=yes"
expect "$(run StagingNext 3.4.0 "(12)")" "scheme=WatchLinkStagingNext version=3.4.0 build=12 upload=yes"
expect "$(run "staging-next 3.4 2" --no-upload)" "scheme=WatchLinkStagingNext version=3.4 build=2 upload=no"
expect "$(run "Staging Next v3.4.1 (3)")" "scheme=WatchLinkStagingNext version=3.4.1 build=3 upload=yes"
expect "$(run "Prod 3.3.0 (5)")" "scheme=WatchLink version=3.3.0 build=5 upload=yes"
expect "$(run "Production 3.3.0(5)")" "scheme=WatchLink version=3.3.0 build=5 upload=yes"

for bad in "Dev 1.0.0 (1)" "Staging 3.3.0" "Staging (1)" "Staging 3 (1)" ""; do
  out=$(run "$bad") && { printf 'FAIL: accepted "%s" -> %s\n' "$bad" "$out"; exit 1; }
  case "$out" in FAILED:*) ;; *) printf 'FAIL: no FAILED line for "%s"\n' "$bad"; exit 1 ;; esac
done

echo OK
