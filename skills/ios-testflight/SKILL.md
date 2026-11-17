---
description: "Archive watchlink-mobile iOS variants from the current checkout and upload them to TestFlight. Args: <Staging|StagingNext|Prod> <version> (<build>), several separated by commas; --no-upload only archives. E.g. /vad4nus:ios-testflight Staging 3.3.0 (1), StagingNext 3.4.0 (2)"
argument-hint: "<Staging|StagingNext|Prod> <version> (<build>)[, ...] [--no-upload]"
model: sonnet
effort: low
disable-model-invocation: true
---

# iOS TestFlight

Archives watchlink-mobile iOS builds from the current checkout and uploads them to TestFlight. Manual only: one archive takes 15 to 20 minutes, and the upload goes to App Store Connect.

## Arguments

One or more items separated by `,`, `;` or new lines. Each item is `<variant> <version> (<build>)`, for example `Staging 3.3.0 (1), StagingNext 3.4.0 (2)`. Case does not matter, the parentheses are optional.

| Variant                                     | Scheme                 |
| ------------------------------------------- | ---------------------- |
| `staging`                                   | `WatchLinkStaging`     |
| `staging-next`, `StagingNext`, `Staging Next` | `WatchLinkStagingNext` |
| `prod`, `production`                        | `WatchLink`            |

- `--no-upload` anywhere: archive only.
- Dev is not supported: it is signed by another team and has no App Store Connect app.
- No arguments, or an item without a version or build: print the argument hint with the example and stop. Never guess a version or a build number.

## Ground rules

- `S="${CLAUDE_PLUGIN_ROOT}/skills/ios-testflight/testflight.sh"` does all the work. Never repeat its steps by hand, and never edit code or `project.yml` to make an archive pass.
- Run `$S` with the Bash sandbox disabled: `xcodebuild` needs signing, DerivedData and the Xcode account.
- Items run strictly one after another: they share Gradle, `~/.konan` and DerivedData.

## Steps

1. **Parse.** For each item run `"$S" --parse-only <item> [--no-upload]`. A `FAILED:` line: show it and stop.

2. **Checkout.** Collect `git rev-parse --show-toplevel`, `git rev-parse --abbrev-ref HEAD`, `git log -1 --format='%h %s'` and `git status --porcelain --untracked-files=no | wc -l`.

3. **Confirm** with one `AskUserQuestion`, header `TestFlight`, in the user's language. List every item (scheme, version, build, upload yes or no), then the checkout path, branch, commit and the count of uncommitted tracked files. Options: build and upload (or build only with `--no-upload`), and cancel. This is the only question.

4. **Run** each item in the background, one at a time, and wait for the completion notification instead of polling with `sleep`:

   ```bash
   "$S" <item> [--no-upload]
   ```

   Use `run_in_background: true` and `dangerouslyDisableSandbox: true`. Tell the user it started: the archive takes 15 to 20 minutes (log `/tmp/testflight-<Scheme>-archive.log`), the upload 2 to 3 more. The archive log stays silent for about 10 minutes while Kotlin/Native links the release framework; `clang++` at about 100% CPU in `ps` means it is working, not hung.

5. **Outcome.** The last line is `RESULT ...` on success. On failure it is `FAILED: <stage>`, preceded by the first error lines. On failure show those lines with their file and line, and skip the remaining items. Do not retry: the script already retries once on a stale Gradle daemon.

6. **Report** a table per item: scheme, version, requested build → `uploaded_build`, minutes, archive path. Xcode raises the build number when the requested one is already taken for that version, so `uploaded_build` can differ. Add every `WARNING:` line. Archives show up in Xcode Organizer.

## Known noise, not failures

- `Upload Symbols Failed` for FirebaseAnalytics, GoogleAppMeasurement, GoogleAdsOnDeviceConversion: binary SPM frameworks ship without dSYMs.
- `No provider associated with App Store Connect user`: the second Apple ID in Xcode has no App Store Connect access.
- Hundreds of Kotlin `warning:` lines.

## Self-check

`skills/ios-testflight/testflight.test.sh` prints `OK` when the item parser is intact. Run it after changing `testflight.sh`.
