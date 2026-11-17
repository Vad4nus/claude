---
description: "Build one watchlink-mobile iOS scheme and launch it on a simulator with the live panel open, or on a connected iPhone. Args: staging|staging-next|dev|prod picks the scheme; --real runs on the connected physical device instead of a simulator; --device <name|udid> picks the simulator or, with --real, the device (default: the booted simulator, else iPhone 17; with --real the only connected device); --no-build relaunches the last build. E.g. /vad4nus:ios-run staging-next --real"
argument-hint: "<staging|staging-next|dev|prod> [--real] [--device <name|udid>] [--no-build]"
model: sonnet
effort: medium
disable-model-invocation: true
---

# iOS Run

Builds one iOS scheme of watchlink-mobile and launches it on a simulator, or with `--real` on a connected iPhone. Manual only: an iOS build takes 10 to 15 minutes on this Mac.

## Arguments

| First argument  | Scheme                 | Bundle id                             |
| --------------- | ---------------------- | ------------------------------------- |
| `staging`       | `WatchLinkStaging`     | `com.watchlink.mobile.ios.staging`     |
| `staging-next`  | `WatchLinkStagingNext` | `com.watchlink.mobile.ios.stagingnext` |
| `dev`           | `WatchLinkDev`         | `com.jetruby.watchlink.mobile`         |
| `prod`          | `WatchLink`            | `com.watchlink.mobile.ios`             |

The scheme comes only from this argument, never from the branch. Missing or unknown → ask with `AskUserQuestion` offering these four, no default.

- `--real` — a connected physical iPhone instead of a simulator. Steps 1, 4 and 6 have a `--real` variant. No live panel and no screenshot: the iOS Simulator tools cannot see a real device.
- `--device <name|udid>` — the simulator. Default: the booted one, else "iPhone 17". With `--real`: a connected device by UDID, name or model ("iPhone 15 Pro"); several phones may share the name "iPhone", so the model or UDID is safer.
- `--no-build` — skip steps 3 to 5 and launch the last build of the scheme.

## Ground rules

- `ROOT=$(git rev-parse --show-toplevel)`; stop if `ROOT/iosApp/project.yml` is missing. Absolute paths everywhere: the session cwd may already be `iosApp/`.
- Run `xcodebuild`, `xcodegen`, `xcrun simctl` and `xcrun devicectl` with the Bash sandbox disabled: they need CoreSimulatorService, CoreDevice and DerivedData.
- Never hand-edit `project.pbxproj`, never record snapshots, never run tests, never edit code to make the build pass.

## Steps

1. **Simulator.** Resolve the UDID:
   - `--device` is a UDID → use it. A name → `xcrun simctl list devices available | grep -E "^ +<name> \(" | grep -oE "[0-9A-F-]{36}" | head -1`.
   - No `--device` → `xcrun simctl list devices booted | grep -oE "[0-9A-F-]{36}" | head -1`, else "iPhone 17" by name.

   Not booted → `xcrun simctl boot <UDID>; open -a Simulator; xcrun simctl bootstatus <UDID> -b`. Then open the live panel with the iOS Simulator `control` tool, action `attach`, on that UDID, before anything slow, so the user watches from the start.

   **`--real` instead:** list the connected devices as `udid model name developer-mode`:

   ```bash
   xcrun devicectl list devices --json-output /tmp/wl-devices.json -q >/dev/null && python3 -c "import json; [print(d['hardwareProperties']['udid'], d['hardwareProperties'].get('marketingName'), d['deviceProperties'].get('name'), d['deviceProperties'].get('developerModeStatus'), sep=' | ') for d in json.load(open('/tmp/wl-devices.json'))['result']['devices'] if d['connectionProperties'].get('tunnelState') == 'connected']"
   ```

   Keep the rows that match `--device` (UDID, model or name), if given. One row → its UDID. Several → `AskUserQuestion` with model and UDID per option. None → stop: connect the iPhone by cable, unlock it and tap Trust. A paired device that is not connected (an iPhone away from Wi-Fi) does not count. Developer mode not `enabled` → stop: Settings → Privacy & Security → Developer Mode, then the phone restarts.

2. **Gradle daemon.** `cd "$ROOT" && ./gradlew --stop -q`. The Xcode build runs Gradle for the KMP frameworks, and a stale daemon breaks moko's asset compile with "Connection refused".

3. **Project.** `(cd "$ROOT/iosApp" && xcodegen generate)` on every run: a branch switch or any Gradle run can leave a stale project or wipe the schemes. Then `xcodebuild -list -project "$ROOT/iosApp/Watchlink.xcodeproj"` must list the scheme. If it does not, stop and say why: `project.yml` creates shared schemes only for targets with `scheme:` (today `WatchLinkStaging` and `WatchLinkStagingNext`), and adding one is an iOS change the user has to ask for.

4. **Build** in the background, then wait for the completion notification instead of polling:

   ```bash
   xcodebuild -project "$ROOT/iosApp/Watchlink.xcodeproj" -scheme <S> -configuration Debug -destination "platform=iOS Simulator,id=<UDID>" build > /tmp/wl-<S>-build.log 2>&1; echo EXIT=$?
   ```

   With `--real`: `-destination "platform=iOS,id=<UDID>" -allowProvisioningUpdates`. Automatic signing then registers the device in the team and fetches a development profile through the Xcode account. A signing error that survives this (`No Account for Team`, `No profiles for`) is fixed in Xcode → Settings → Accounts, never in `project.yml`: show it and stop.

   Tell the user it is running: about 11 minutes cold, and a new worktree always starts with cold DerivedData. Outcome: `grep -E "error:|^e: |BUILD (SUCCEEDED|FAILED)" /tmp/wl-<S>-build.log | head -20` (`e: file://…` is a Kotlin compile error from the KMP framework phase).

   If the sandbox cannot be disabled, the iOS Simulator `build` tool (`project_path`, `scheme`, `device`) replaces this step; its `build_status` returns the errors and the `.app` path.

5. **Self-heal**, once per cause, then stop:

   | Log contains                                                     | Fix, then rebuild  |
   | ---------------------------------------------------------------- | ------------------ |
   | `Connection refused`, `Code=61`, `can't compile assets`          | `./gradlew --stop` |
   | `does not contain a scheme`, `Build input files cannot be found` | step 3 again       |

   Anything else, or the same failure twice: show the first `error:` lines with their file and line, and stop. Exception: the start message named an implement session (orchestrate does) and the errors point at source files under `$ROOT` → step 5a instead.

5a. **Fix loop (orchestrate only)**, up to 5 rounds. This session still never edits code: the implement session fixes, this one rebuilds.

   1. `SendMessage` to the implement session id from the start message: `BUILD-FAILED <n>/5 from ios-run, scheme <S>, log /tmp/wl-<S>-build.log:`, the error lines with file and line (at most 20), then: `This pipeline includes an iOS run, so making iosApp/ compile is in scope; change only what these errors need. Fix them in this worktree, run kmp-verify, then SendMessage to the session in this message's from= with "BUILD-FIXED: <one line per change>" and end your turn with a short summary. Do not print IMPLEMENT-PLAN DONE. A fix that needs the user's decision: ask the user first, send BUILD-FIXED after; if nobody can answer (a night run), send "BUILD-NOT-FIXED: <why>" instead.`
   2. One line to the user: the build failed, the implement session is fixing it (round n of 5), the rebuild starts by itself. End the turn without `IOS-RUN DONE`.
   3. A message starting with `BUILD-FIXED` → back to step 2 (step 3's xcodegen picks up new Swift files), then build and launch as usual.
   4. A message starting with `BUILD-NOT-FIXED`, or still failing after round 5 → stop and report the errors of every round and the reason given.

6. **Launch.** App path:

   ```bash
   xcodebuild -project "$ROOT/iosApp/Watchlink.xcodeproj" -scheme <S> -configuration Debug -destination "platform=iOS Simulator,id=<UDID>" -showBuildSettings | grep -E " (TARGET_BUILD_DIR|FULL_PRODUCT_NAME|PRODUCT_BUNDLE_IDENTIFIER) = "
   ```

   With `--real`, use the step 4 `--real` destination; `TARGET_BUILD_DIR` then ends in `Debug-iphoneos`. The query can take a few minutes while Xcode resolves packages.

   The app is `<TARGET_BUILD_DIR>/<FULL_PRODUCT_NAME>`. With `--no-build`, if it does not exist, say there is no build of this scheme yet and stop. Launch with the iOS Simulator `control` tool, action `launch`, `app_path` and the UDID. Then take a `screenshot` and confirm the app is on screen, not the home screen after a crash.

   **`--real` instead:**

   ```bash
   xcrun devicectl device install app --device <UDID> "<app>" && xcrun devicectl device process launch --device <UDID> --terminate-existing <PRODUCT_BUNDLE_IDENTIFIER>
   ```

   A locked phone fails the launch: ask the user to unlock it and launch once more. Then wait 5 seconds and confirm it is still running: `xcrun devicectl device info processes --device <UDID> | grep -c "/<FULL_PRODUCT_NAME>/"` is 1 or more. 0 means it crashed on start: say so and stop.

7. **Report:** scheme, simulator or device (model and UDID), build time or "skipped", fix rounds with what each fixed, launched yes or no. Its very last line is `IOS-RUN DONE`, also after a failure that stopped the run, never while waiting for `BUILD-FIXED`.
