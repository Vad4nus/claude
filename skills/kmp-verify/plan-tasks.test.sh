#!/usr/bin/env bash
# Self-check for plan-tasks.sh. Run from anywhere: prints OK or the first mismatch.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
run() { printf '%s\n' "$@" | "$here/plan-tasks.sh" -; }
expect() { [ "$1" = "$2" ] || { printf 'FAIL\n  got:  %s\n  want: %s\n' "$1" "$2"; exit 1; }; }

expect "$(run shared/src/commonMain/kotlin/A.kt resources/src/commonMain/moko-resources/base/strings.xml)" \
"gradle: generateMR :shared:testDebugUnitTest :androidApp:compileDevDebugKotlin detekt
xcodegen: no
swiftlint:"

expect "$(run data/src/commonMain/kotlin/B.kt domain/src/commonTest/kotlin/C.kt androidApp/src/main/AndroidManifest.xml)" \
"gradle: :data:testDebugUnitTest :androidApp:compileDevDebugKotlin detekt :domain:testDebugUnitTest
xcodegen: no
swiftlint:"

expect "$(run iosApp/Sources/Deleted.swift iosApp/README.md)" \
"gradle:
xcodegen: yes
swiftlint:"

swift_file=$(mktemp -d)/iosApp/Sources/Kept.swift
mkdir -p "$(dirname "$swift_file")" && touch "$swift_file"
(cd "${swift_file%/iosApp/*}" && expect "$(run iosApp/Sources/Kept.swift iosApp/project.yml)" \
"gradle:
xcodegen: yes
swiftlint: iosApp/Sources/Kept.swift")

expect "$(run '')" \
"gradle:
xcodegen: no
swiftlint:"

echo OK
