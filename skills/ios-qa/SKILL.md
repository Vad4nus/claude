---
description: "Check a fresh watchlink-mobile iOS build on the simulator the way a tester would: derive 3 to 7 checks from the plan, its manual checks and the changed screens, tap through them in the running app and report pass, fail or not run per check. Never edits code, never builds. Args: staging|staging-next|dev|prod picks the app; --device <name|udid> picks the simulator (default: the booted one); the rest is the plan path or what to check. E.g. /vad4nus:ios-qa staging-next thoughts/shared/plans/2026-11-10-W30-1113.md"
argument-hint: "<staging|staging-next|dev|prod> [--device <name|udid>] <plan path | what to check>"
model: sonnet
effort: medium
disable-model-invocation: true
---

# iOS QA

A short hands-on check of the app already installed on a simulator, usually right after `/vad4nus:ios-run`. Simulator only: the iOS Simulator tools cannot drive a real iPhone.

## Ground rules

- Never edit code, build, record snapshots or run tests. A failure is reported, not fixed.
- Never type credentials. The login screen → ask the user with `AskUserQuestion` to sign in in the simulator panel, then go on.
- The app talks to the flavor's real backend. Prefer read-only checks. A check may change server data (post, comment, bid, chat message, follow, profile edit) only on `dev`, `staging` or `staging-next`, only when the change under test needs it, with content that reads as a test. Never: purchases or payments, deleting or reporting anything this run did not create, account settings. On `prod`: read-only checks only.
- `xcrun simctl` runs with the Bash sandbox disabled.

## Setup

1. The bundle id comes from the flavor, with the table in `../ios-run/SKILL.md` (relative to this skill's base directory). Missing or unknown flavor → ask with `AskUserQuestion` offering the four, no default.
2. UDID: `--device` resolved as in ios-run step 1, else `xcrun simctl list devices booted | grep -oE "[0-9A-F-]{36}" | head -1`. None booted → stop: run `/vad4nus:ios-run <flavor>` first.
3. iOS Simulator `control` tool: `attach` on that UDID, then `screenshot`. The app is not on screen → `xcrun simctl launch <UDID> <bundle id>`. Not installed → stop: run ios-run first.

## Checks

1. Sources: the plan (manual verification items, the screens each phase changes), the manual checks list if the start message carries one, and `git status --short`.
2. Pick 3 to 7 checks a tester can do on this simulator in a few minutes: the change under test first, then one smoke check of a screen next to it. Each: screen, steps, expected result. What a simulator cannot show (push notifications, camera, purchases, another user's side, states only the backend can create) goes to the list as "not run" with the reason.
3. Post the list to the user, then run it without waiting for approval.

## Running

Per check: `screenshot`, act (`tap`, `swipe`, `text`, `button`, in device points from the latest screenshot), `screenshot`, compare with the expected result.

- Fail → `xcrun simctl io <UDID> screenshot /tmp/wl-qa-<n>.png`, note what was on screen instead, go on to the next check.
- The home screen instead of the app is a crash → fail, `xcrun simctl launch <UDID> <bundle id>`, go on.
- A step you cannot find on screen after two tries → "not run" with what was missing; never guess a pass.

## Report

A table: number, check, verdict (pass, fail, not run), what was seen. Then each failure with its steps and screenshot path. Its very last line is `IOS-QA DONE`, also when the run stopped early.
