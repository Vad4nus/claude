---
description: "Archive the watchlink-mobile Prod iOS app from the current checkout and upload it to App Store Connect, ready to attach to an App Store version. What's New, submission and release stay manual. Args: <version> (<build>). E.g. /vad4nus:ios-appstoreconnect 3.3.0 (5)"
argument-hint: "<version> (<build>)"
model: sonnet
effort: low
disable-model-invocation: true
---

# iOS App Store Connect

Archives the Prod scheme `WatchLink` from the current checkout and uploads it to App Store Connect. It runs the same script as `ios-testflight`: the upload is not "TestFlight internal only", so the build lands in TestFlight and can be selected for the App Store version. This command never touches the App Store version, What's New, review submission or release; the user does those in App Store Connect.

## Arguments

`<version> (<build>)`, for example `3.3.0 (5)`. A leading `Prod` is accepted. No version or build: print the argument hint with the example and stop. Never guess either.

## Ground rules

- `S="${CLAUDE_PLUGIN_ROOT}/skills/ios-testflight/testflight.sh"` does all the work. Never repeat its steps by hand, and never edit code or `project.yml` to make an archive pass.
- Run `$S` with the Bash sandbox disabled: `xcodebuild` needs signing, DerivedData and the Xcode account.
- The `WatchLink` scheme exists only where Xcode has autocreated it (the main checkout). In a fresh worktree the script stops with that reason; pass it on.

## Steps

1. **Parse.** `"$S" --parse-only Prod <version> <build>`. A `FAILED:` line: show it and stop.

2. **Checkout.** Collect `git rev-parse --show-toplevel`, `git rev-parse --abbrev-ref HEAD`, `git log -1 --format='%h %s'` and `git status --porcelain --untracked-files=no | wc -l`.

3. **Confirm** with one `AskUserQuestion`, header `App Store`, in the user's language: `WatchLink <version> (<build>)` goes to App Store Connect from this checkout path, branch and commit, with the count of uncommitted tracked files. Options: upload, and cancel.

4. **Run** in the background and wait for the completion notification instead of polling with `sleep`:

   ```bash
   "$S" Prod <version> <build>
   ```

   Use `run_in_background: true` and `dangerouslyDisableSandbox: true`. Tell the user it started: the archive takes 15 to 20 minutes (log `/tmp/testflight-WatchLink-archive.log`), the upload 2 to 3 more. The log stays silent for about 10 minutes while Kotlin/Native links the release framework; that is not a hang.

5. **Outcome.** `RESULT ...` on success. `FAILED: <stage>` after the first error lines on failure: show them with file and line, and stop. Do not retry: the script already retries once on a stale Gradle daemon.

6. **Report:** version, requested build → `uploaded_build` (Xcode raises it when the number is taken), minutes, archive path, every `WARNING:` line. Then the manual steps left in App Store Connect:
   1. Wait for the "has completed processing" email, usually 10 to 30 minutes.
   2. App Store tab → version `<version>` (create it with "+" if missing) → Build → select `<uploaded_build>`.
   3. Fill in What's New, submit for review, release by hand after approval.

## Known noise, not failures

- `Upload Symbols Failed` for FirebaseAnalytics, GoogleAppMeasurement, GoogleAdsOnDeviceConversion.
- `No provider associated with App Store Connect user`: the second Apple ID in Xcode.
- Hundreds of Kotlin `warning:` lines.
