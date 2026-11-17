#!/usr/bin/env bash
# Maps the files changed since <base> (default HEAD, untracked included) to targeted checks.
# Pass `-` to read the file list from stdin instead of git.
set -eu

if [ "${1:-}" = "-" ]; then
  files=$(cat)
else
  files=$( { git diff --name-only "${1:-HEAD}" --; git ls-files --others --exclude-standard; } | sort -u )
fi

case "$(uname -m)" in arm64) ios_target=IosSimulatorArm64 ;; *) ios_target=IosX64 ;; esac

tasks="" swift="" xcodegen=no
add() { case " $tasks " in *" $1 "*) ;; *) tasks="$tasks $1" ;; esac; }

while IFS= read -r f; do
  case "$f" in
    resources/*) add generateMR; add :androidApp:compileDevDebugKotlin ;;
    shared/*|domain/*|data/*) add ":${f%%/*}:testDebugUnitTest"; add :androidApp:compileDevDebugKotlin ;;
    core/*|logger/*|androidApp/*|gradle/*|*.gradle.kts) add :androidApp:compileDevDebugKotlin ;;
    diHelper/*) add ":diHelper:compileKotlin$ios_target" ;;
    iosApp/project.yml) xcodegen=yes ;;
    iosApp/*.swift) xcodegen=yes; if [ -f "$f" ]; then swift="$swift $f"; fi ;;
  esac
  case "$f" in *.kt|*.kts) add detekt ;; esac
done <<EOF
$files
EOF

# generateMR goes first: the compile and test tasks read what it generates.
case " $tasks " in *" generateMR "*) tasks=" generateMR${tasks/ generateMR/}" ;; esac

echo "gradle:$tasks"
echo "xcodegen: $xcodegen"
echo "swiftlint:$swift"
