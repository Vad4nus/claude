---
description: "Verify Kotlin Multiplatform, Android and Swift changes in watchlink-mobile with targeted checks picked from the changed files: unit tests of the touched modules, Android compile, detekt, xcodegen and SwiftLint. Use after editing code in watchlink-mobile, or when implement-plan or validate-plan reach verification. Never runs the full ./gradlew test. Args: --base <ref> checks everything changed since <ref>, committed or not (default: uncommitted and untracked files only). E.g. /vad4nus:kmp-verify --base main"
argument-hint: "[--base <ref>]"
---

# KMP Verify

Run the cheapest checks that cover the change and report them as a table. Read-only toward the code: no fixes, no commits.

No `model:` pin on purpose: when implement-plan or validate-plan load this skill mid-turn, a pin would switch the model for the rest of their turn.

## Steps

1. **Repo check.** `ROOT=$(git rev-parse --show-toplevel)`. Without `ROOT/gradlew` and `ROOT/iosApp/project.yml` this is not watchlink-mobile: say so and stop. Use absolute paths from here on; the session cwd may already be `iosApp/`.

2. **Pick the checks.** From `ROOT`:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/skills/kmp-verify/plan-tasks.sh" <ref from --base, or nothing>
   ```

   It prints three lines: `gradle:` tasks, `xcodegen: yes|no`, `swiftlint:` the changed Swift files that still exist. Without `--base`, the change set is uncommitted plus untracked files. All three empty → report "nothing to verify" and stop.

3. **Gradle**, when the `gradle:` line lists tasks. From `ROOT`, in the background, then wait for the completion notification (this takes minutes):

   ```bash
   ./gradlew --stop -q; ./gradlew <tasks> --continue > /tmp/kmp-verify.log 2>&1; echo EXIT=$?
   ```

   `--stop` first: a stale daemon breaks moko's asset compile with "Connection refused". `--continue` keeps one failure from hiding the rest. Read the outcome with `grep -E "^> Task .* FAILED|BUILD (SUCCESSFUL|FAILED)|tests completed|^e: |error:" /tmp/kmp-verify.log`, then the failing test names and their first assertion lines.

4. **Xcode project**, when `xcodegen: yes`, and only after Gradle, because a Gradle run can wipe the shared schemes: `(cd "$ROOT/iosApp" && xcodegen generate)`.

5. **SwiftLint**, when the `swiftlint:` line lists files: `(cd "$ROOT/iosApp" && swiftlint lint --quiet --force-exclude <paths relative to iosApp/>)`. Lint only. If violations are autocorrectable, suggest `swiftlint --fix` on those files; do not run it.

   If Gradle, xcodegen or SwiftLint fail on sandbox or permission errors rather than on the code, rerun that command with the sandbox disabled.

6. **Report:**

   | Check | Result | Notes |
   | ----- | ------ | ----- |
   | `:shared:testDebugUnitTest` | PASS / FAIL / not run | failing tests, first error |

   Known pre-existing: 2 failures in `NetworkClientAPIWebSocketTest` (`:data:testDebugUnitTest`). Mark them "pre-existing", not a regression. Any other failure belongs to the change until shown otherwise.

7. **Close**, only when the user invoked this skill directly. When another skill loaded it, return the report and let the caller continue.
   - `data/` or `shared/` constructors or DI modules changed: compile and unit tests do not catch Koin cycles. Say the app has to be launched to prove there is none.
   - Kotlin or Swift changed: ask whether to build iOS (`/vad4nus:ios-run <scheme>`). Offer snapshot recording only after an iOS build of the latest edits that the user has checked.

## Never

- `./gradlew test` or `./gradlew build`: they compile every flavor, take ~25 minutes, and run out of memory here.
- xcodebuild, iOS tests, snapshot recording.
- Editing `project.pbxproj`.

## Self-check

`skills/kmp-verify/plan-tasks.test.sh` prints `OK` when the file-to-check mapping is intact. Run it after changing `plan-tasks.sh`.
