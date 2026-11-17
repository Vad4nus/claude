#!/usr/bin/env bash
# Archives one watchlink-mobile iOS variant and uploads it to TestFlight.
# Usage: testflight.sh [--parse-only] [--no-upload] "<Staging|StagingNext|Prod> <version> (<build>)"
# The spec may also come as separate words: Staging 3.3.0 1
set -u

parse_only=no upload=yes spec=""
for a in "$@"; do
  case "$a" in
    --parse-only) parse_only=yes ;;
    --no-upload) upload=no ;;
    *) spec="$spec $a" ;;
  esac
done

fail() { echo "FAILED: $*"; exit 1; }
phase() { echo "[$(date +%H:%M:%S)] $*"; }
errors() { grep -E "error:|\*\* (ARCHIVE|EXPORT) FAILED" "$1" | head -15; }
pb() { /usr/libexec/PlistBuddy -c "Print :$1" "$2" 2>/dev/null; }

spec=$(printf '%s' "$spec" | tr '[:upper:]' '[:lower:]')
re='^ *(staging[-_ ]?next|staging|prod|production) +v?([0-9]+\.[0-9]+(\.[0-9]+)?) *\(? *([0-9]+) *\)? *$'
[[ $spec =~ $re ]] || fail "cannot parse '${spec# }'. Expected e.g. \"Staging 3.3.0 (1)\"; variants: staging, staging-next, prod"
case "${BASH_REMATCH[1]}" in
  staging) scheme=WatchLinkStaging ;;
  prod|production) scheme=WatchLink ;;
  *) scheme=WatchLinkStagingNext ;;
esac
version=${BASH_REMATCH[2]} build=${BASH_REMATCH[4]}
echo "scheme=$scheme version=$version build=$build upload=$upload"
[ "$parse_only" = yes ] && exit 0

root=$(git rev-parse --show-toplevel 2>/dev/null) || fail "not inside a git checkout"
[ -f "$root/iosApp/project.yml" ] || fail "$root is not watchlink-mobile (no iosApp/project.yml)"
proj="$root/iosApp/Watchlink.xcodeproj"
log="/tmp/testflight-$scheme"
total=$SECONDS

phase "project: gradle --stop, xcodegen"
(cd "$root" && ./gradlew --stop -q) >/dev/null 2>&1
(cd "$root/iosApp" && xcodegen generate --quiet) || fail "xcodegen generate"
xcodebuild -list -project "$proj" 2>/dev/null | grep -qE "^ +$scheme\$" \
  || fail "no scheme $scheme in $proj. project.yml shares only WatchLinkStaging and WatchLinkStagingNext; WatchLink exists once Xcode autocreates it (open this checkout's project in Xcode)"

dir=~/Library/Developer/Xcode/Archives/$(date +%F)
archive="$dir/$scheme $version ($build) $(date +%H-%M-%S).xcarchive"
mkdir -p "$dir"
do_archive() {
  xcodebuild archive -project "$proj" -scheme "$scheme" -configuration Release \
    -destination 'generic/platform=iOS' -archivePath "$archive" -allowProvisioningUpdates \
    MARKETING_VERSION="$version" CURRENT_PROJECT_VERSION="$build" > "$log-archive.log" 2>&1
}

phase "archive: about 15-20 min, log $log-archive.log"
start=$SECONDS
if ! do_archive; then
  grep -qE "Connection refused|Code=61|can't compile assets" "$log-archive.log" || { errors "$log-archive.log"; fail "archive"; }
  phase "stale Gradle daemon, retrying once"
  (cd "$root" && ./gradlew --stop -q) >/dev/null 2>&1
  rm -rf "$archive"
  do_archive || { errors "$log-archive.log"; fail "archive"; }
fi
phase "archive done in $(( (SECONDS - start) / 60 )) min: $archive"

got_version=$(pb ApplicationProperties:CFBundleShortVersionString "$archive/Info.plist")
got_build=$(pb ApplicationProperties:CFBundleVersion "$archive/Info.plist")
[ "$got_version" = "$version" ] && [ "$got_build" = "$build" ] \
  || fail "archive has $got_version ($got_build), expected $version ($build)"
echo "bundle=$(pb ApplicationProperties:CFBundleIdentifier "$archive/Info.plist")"
for ext in "$archive"/Products/Applications/*.app/PlugIns/*.appex; do
  [ -d "$ext" ] || continue
  ext_build=$(pb CFBundleVersion "$ext/Info.plist")
  [ "$ext_build" = "$build" ] || echo "WARNING: $(basename "$ext") has build $ext_build, the app has $build; App Store Connect may warn about the mismatch"
done

if [ "$upload" = no ]; then
  echo "RESULT scheme=$scheme version=$version build=$build uploaded=no minutes=$(( (SECONDS - total) / 60 )) archive=$archive"
  exit 0
fi

tmp=$(mktemp -d)
cat > "$tmp/ExportOptions.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key><string>app-store-connect</string>
    <key>destination</key><string>upload</string>
    <key>teamID</key><string>3734H6URQ8</string>
    <key>signingStyle</key><string>automatic</string>
    <key>uploadSymbols</key><true/>
    <key>manageAppVersionAndBuildNumber</key><true/>
</dict>
</plist>
EOF

phase "upload to App Store Connect: about 2-3 min, log $log-upload.log"
start=$SECONDS
xcodebuild -exportArchive -archivePath "$archive" -exportOptionsPlist "$tmp/ExportOptions.plist" \
  -exportPath "$tmp/export" -allowProvisioningUpdates > "$log-upload.log" 2>&1 \
  || { errors "$log-upload.log"; fail "upload"; }
uploaded=$(pb Distributions "$archive/Info.plist" | grep -oE "uploadedBuildNumber = [0-9]+" | tail -1 | grep -oE "[0-9]+$")
phase "upload done in $(( (SECONDS - start) / 60 )) min"
echo "RESULT scheme=$scheme version=$version build=$build uploaded_build=${uploaded:-unknown} minutes=$(( (SECONDS - total) / 60 )) archive=$archive"
