# vad4nus roadmap

## Done (2026-10-08)

- Repo created: cross-model-deliberation added (`4a8b0f8`).
- Old `~/.claude/skills/cross-model-deliberation` moved to `~/.Trash/cross-model-deliberation-2026-10-08`.
- `~/.claude/settings.json` default model: `opus`.

Facts that shape the design:

- Skill `model:` lasts for the rest of the current turn only; the session model resumes on the next user prompt. It cannot reference arguments.
- A model-invoked skill with its own `model:` would take over the caller's turn, so helper skills (kmp-verify) carry no model pin.
- codebase-memory-mcp: `auto_watch = true`, `auto_index = false` -> desktop worktrees are never indexed until someone calls `index_repository`.
- `~/.codex/config.toml`: `gpt-6-astra`, `model_reasoning_effort = "high"`.

## Phase 1: create-plan — done 2026-10-08

1. Frontmatter: `model: opus`, `effort: high`, keep `disable-model-invocation: true`, add `argument-hint: [--agents haiku|sonnet|opus] [--codex-effort high|xhigh|max] [--no-codex] <task>`.
2. Parse and strip the flags before the Command Contract heuristic runs.
3. Step 0: call MCP `index_repository` with `git rev-parse --show-toplevel`. On failure say so and continue.
4. `--agents <m>`: pass `model: <m>` on every research Agent call. Without the flag the agents' own frontmatter applies (Phase 3).
5. Step 2.5 ladder: add a Gradle row -> `vad4nus:kmp-verify`; never full `./gradlew test`.
6. Step 5: ask via `AskUserQuestion` (approve / adjust) so the pinned turn continues through Step 7c.
7. New Step 7c, after the 7b verdict is PASS or FLAG: Codex review of the draft through `vad4nus:cross-model-deliberation` plan-review mode, effort from `--codex-effort` (default `xhigh`); skipped on `--no-codex`. Fix the plan or surface disagreements; record the outcome in `VERIFICATION.md`.
8. Step 8 close: print both `/vad4nus:implement-plan <path>` and "`/clear`, then the same command".

## Phase 2: cross-model-deliberation plan-review mode — done 2026-10-08

1. New "Plan review mode" section, entered only when create-plan calls it: trigger gate counts as satisfied (user opted in via create-plan), effort from the caller instead of the hardcoded `max`.
2. Brief: plan path + `thoughts/groom/TASK.md`; Codex reads the repo read-only and checks requirement coverage, `file:line` accuracy, phase order, missed edge cases. Keep the one-rebuttal limit.
3. Fix stale text: the Codex default effort is `high`, not `xhigh`.

## Phase 3: implement-plan, validate-plan, the rest — done 2026-10-08

1. implement-plan: `model: sonnet`, `effort: high`, stays manual-only; Step 0 `index_repository`; `<verification>`: replace "run full suite" with `vad4nus:kmp-verify` on Gradle/KMP repos.
2. validate-plan: `model: sonnet`, `effort: medium`; same verification swap.
3. research-codebase: `claude-sonnet-4-6` -> `sonnet`.
4. Agents: `claude-sonnet-4-6` -> `sonnet` (analyzer, pattern-finder, thoughts-analyzer, web-search-researcher); locators stay `claude-haiku-4-5`.
5. plan-status, plan-archive: keep `claude-haiku-4-5`.

## Phase 4: kmp-verify (new skill) — done 2026-10-08

Model-invocable, no model pin. Args: `[--base <ref>]` (default: uncommitted + untracked changes).

1. Changed files -> task set, run in ONE Gradle invocation with `--continue` after `./gradlew --stop`:
   - `resources/` -> `generateMR` first
   - `shared/` -> `:shared:testDebugUnitTest`
   - `data/` -> `:data:testDebugUnitTest` (2 `NetworkClientAPIWebSocketTest` failures are pre-existing)
   - `domain/` -> its unit-test task (confirm the name with `./gradlew :domain:tasks --all`)
   - any Kotlin under shared/domain/data/core/resources/androidApp -> `:androidApp:compileDevDebugKotlin`
   - any `.kt`/`.kts` -> root `detekt`
2. `iosApp/` changed: `xcodegen generate` in `<root>/iosApp` (absolute path), `swiftlint lint` on the changed Swift files only. No xcodebuild.
3. Hard rule: never `./gradlew test` (OOMs on release flavors here).
4. Report a task -> PASS/FAIL table, pre-existing failures marked.
5. Close: if `data/` constructors changed, warn that compile/tests miss Koin cycles (launch the app). Then ask: build iOS? Snapshots are offered only after a fresh build the user has checked.

## Phase 5: ios-run (new skill) — done 2026-10-08

`disable-model-invocation: true` (iOS builds only on request), `model: sonnet`, `effort: medium`.
Args: `<staging|staging-next|dev|prod> [--device <name|udid>] [--no-build]`.

1. Scheme comes only from the argument, never from the branch: `staging` -> `WatchLinkStaging`, `staging-next` -> `WatchLinkStagingNext`, `dev` -> `WatchLinkDev`, `prod` -> `WatchLink`. Missing or unknown -> ask with these four options.
2. Device: booted simulator, else "iPhone 17". Boot if needed (`simctl boot`, `open -a Simulator`, `simctl bootstatus -b`), then iOS Simulator `attach` BEFORE building.
3. `./gradlew --stop -q` at repo root, then `xcodegen generate` in `<root>/iosApp` (every run: branch switches and Gradle runs wipe schemes).
4. `xcodebuild -project <root>/iosApp/Watchlink.xcodeproj -scheme <S> -destination 'platform=iOS Simulator,id=<UDID>' build`, log to `/tmp/wl-<scheme>-build.log`, in background (~11 min cold, new worktree = cold DerivedData).
5. Self-heal once, then stop: `Connection refused` / `Code=61` / `can't compile assets` -> `./gradlew --stop`; `does not contain a scheme` / `Build input files cannot be found` -> xcodegen. Anything else: show the first `error:` lines.
6. App path from `-showBuildSettings` (`TARGET_BUILD_DIR` + `FULL_PRODUCT_NAME`), launch via iOS Simulator `launch`, screenshot to confirm.
7. xcodebuild/xcodegen/simctl need the Bash sandbox disabled. Never hand-edit `project.pbxproj`, never record snapshots, never run tests.
8. Evaluate the iOS Simulator MCP `build` tool as a replacement for step 4.

## Phase 6: cleanup — items 1-2 done 2026-10-08

1. Remove the `cbm-subagent-reminder` SubagentStart hook from `~/.claude/settings.json` (research agents have no MCP tools; the Grep/Glob augmenter stays).
2. Keep `cbm-session-reminder`.

## Verify each phase

- `claude plugin validate ~/StudioProjects/vad4nus-claude`
- `/reload-plugins`, then run the changed skill on a small real task
- kmp-verify: dry run on an existing diff; ios-run: one real staging-next run

## Phase 7: Jira Server fetch — done 2026-10-08

New skill `/vad4nus:fetch-server-jira-tasks [KEY]` backed by a bundled Python MCP server.
- `mcp/jira_server.py`: PEP 723, two read-only tools (`my_sprint_issues`, `fetch_issue`), atomic overwrite, login-page detection, `--self-test` flag.
- `plugin.json`: four `userConfig` fields (url default `https://jira.jetru.by`, PAT sensitive, project, download dir), `mcpServers.jira-server` stdio entry.
- `skills/fetch-server-jira-tasks/SKILL.md`: haiku, effort low, disable-model-invocation.
- Cloud Jira (`fetch-cloud-jira-tasks`) is explicitly out of scope; see "Still open".
- Config workaround: Claude Code 2.1.293–2.1.294 substitutes only defaults and `--settings` values into the plugin MCP env, never values saved in user `pluginConfigs` (verified: `--settings` project `ZZZ` arrived, saved `W30` did not). The server reads `pluginConfigs` from `settings.json` itself and the PAT from Keychain service `vad4nus-jira-server`.
- Rejected: a Claude Desktop Extension (`.mcpb`) has an editable form but is not handed to Code tab sessions.
- Fixed 2026-10-20: constant 401s with a valid PAT. Claude Code did pass the PAT once saved in the plugin form (sensitive values arrive, unlike plain saved options) and that stale env token beat the Keychain; the server also read the token only at startup. Now the PAT field is gone from `userConfig`, the Keychain is read on every tool call, env `JIRA_TOKEN` is only a fallback.
- Verified on W30-891: PAT attachment download returns 200 directly (no login redirect); the sprint field is found by its `:gh-sprint` schema suffix (`com.pyxis.greenhopper.jira:gh-sprint` on Server).

## Phase 8: ios-testflight — done 2026-10-08

New skill `/vad4nus:ios-testflight <Staging|StagingNext|Prod> <version> (<build>)[, ...] [--no-upload]`, built from `watchlink-mobile/thoughts/ios-archive-testflight-context.md`.
- `testflight.sh` parses the item and runs `gradlew --stop` and xcodegen. It archives with `MARKETING_VERSION` and `CURRENT_PROJECT_VERSION` passed on the command line, then checks the archived version and build. It warns if an extension's build number differs from the app's. It uploads with `-exportArchive` and reads `uploadedBuildNumber` from the archive. It retries the archive once on a stale Gradle daemon. `testflight.test.sh` checks the parser.
- `SKILL.md`: sonnet, effort low, disable-model-invocation. One confirmation showing branch, commit and the dirty-file count before the 20-minute run.
- Builds the current checkout only, with no branch switching. Dev is not supported.

## Phase 9: implement-plan finish stage — done 2026-10-09

- `skills/thermo-nuclear-code-quality-review/`: Cursor's skill, verbatim with its MIT license; also usable alone as `/vad4nus:thermo-nuclear-code-quality-review`.
- `agents/thermo-nuclear-code-quality-review.md`: opus, read-only. Diffs against a given BASE, including uncommitted and untracked files. Reads the rubric from the path it is given and returns findings with remedies and `needs-user` tags.
- implement-plan records BASE at pre-flight. Once all phases are checked, `<finish>` runs these steps:
  1. validate-plan, read from the sibling skill file because it is not model-invocable.
  2. Up to 2 fix rounds.
  3. One review.
  4. Every finding applied automatically, except `needs-user`, behavior changes and anything out of scope.
  5. A second verification. A review change that still breaks a check is reverted.
- User decisions: "verify" means validate-plan; review findings are applied automatically.

## Phase 10: ios-appstoreconnect — done 2026-10-12

- `/vad4nus:ios-appstoreconnect <version> (<build>)`: Prod only. It is a thin skill over `ios-testflight/testflight.sh`. The upload is not "TestFlight internal only", so the build is selectable for the App Store version. Its report lists the manual App Store Connect steps that follow.
- User decisions: upload only. What's New, review submission and release are done by hand. No App Store Connect API key is needed, and none exists on this Mac.

## Phase 11: orchestrate — done 2026-10-20

- `/vad4nus:orchestrate <flavor> [--no-ios] [--real] [--device x] [create-plan flags] <task>`: a thin sonnet dispatcher. Each stage is the real command in its own Desktop side session (`start_session`, same worktree, opened in split view), so each gets its own model pin and a clean context; questions are answered in the side session. The dispatcher waits for turn-end notices and moves on when the stage's last-line marker appears: create-plan `--auto` prints `PLAN: <path>`, implement-plan `IMPLEMENT-PLAN DONE`, ios-run `IOS-RUN DONE`.
- create-plan `--auto` (new): no Step 5 approval, no Step 8 iteration; open Codex disagreements still go through `AskUserQuestion`.
- User decisions: the flavor is required and checked first (scheme via xcodegen + `xcodebuild -list` at once); reuse the existing commands; side sessions. `--no-ios` allows omitting the flavor (my default, not confirmed).
- First real run 2026-10-20: the plan stage worked; stage 2 stalled on a card. `start_session` in a turn started by a turn-end note returns "Start sessions only on the user's own words" and falls back to a proposal card. Fixed 2026-10-21: all stage sessions are opened in the first, user-started turn; stages 2 and 3 wait and get a `GO` cross-session message, then follow their command's SKILL.md file, with model and effort set on the session up front (`set_session_model` / `set_session_effort`, no prompt when cheaper than or equal to the dispatcher). The same run's stage 2 also hit a full disk (ENOSPC).
- Build-fix loop 2026-11-10: the W30-1113 run's iOS build failed on a Swift call missing two new KMP params, and ios-run stopped for the user. Now ios-run (step 5a), given the implement session id in its GO, sends `BUILD-FAILED n/5` with the errors straight to the implement session; that session fixes, runs kmp-verify and replies `BUILD-FIXED` to the `from=` id in the incoming `<cross-session-message>`; ios-run rebuilds. Max 5 rounds (raised from 3 on the user's request); only errors in source files under the repo, signing and scheme failures still stop. The dispatcher only narrates. Also seen in the 2026-10-21 run: `set_session_model` wants the picker id (`claude-sonnet-5-5`), `sonnet` is refused.
- Stage 4, testing, 2026-11-11: new `/vad4nus:ios-qa <flavor> [--device] <plan | what to check>`. After ios-run launched the app on a simulator, it derives 3 to 7 checks from the plan, implement-plan's manual checks and `git status`, taps through them with the iOS Simulator tool and reports pass, fail or not run, `IOS-QA DONE` last. Never types credentials (asks the user to sign in in the panel), server writes only on dev/staging/staging-next and only when the change needs it, prod read-only, never purchases. Skipped by `--no-testing`, `--no-ios`, `--real` (simulator tools cannot drive a device) or when the app did not launch. Failed checks are only reported, no fix loop yet. ios-run's flavor table now carries the bundle id.
- `--night` 2026-11-11: every question up front, then the run goes on alone. First turn: side sessions to `auto` (new sessions start in `default`, the first prompt would wait all night), keep-awake setting, free disk, one AskUserQuestion (iOS builds mid-implementation, KMP extraction of duplicated logic, the iPhone with `--real`). The plan's own questions come in its session; on `PLAN:` the dispatcher says the user can go. Every GO carries a night note: minor decisions → safe default, important → deferred and listed, done marker anyway. A stage asking anyway gets one nudge, then the run ends with the report. Any deferred question skips QA (my reading of the user's "в этом случае QA не нужно"). ios-run 5a gains `BUILD-NOT-FIXED` so a deferred build fix cannot leave ios-run waiting. Unverified: whether keep-awake holds while ios-run's session waits on a background build.
- Probed 2026-10-20: `start_session` is referenced by other Desktop tools but not exposed in an old session; the user runs orchestrate in a fresh one. A `claude` CLI in an app Terminal tab runs a slash command from its start prompt but fails here with ECONNREFUSED (API billing), so terminal sessions are not a fallback. No start_session → stop, never run the stages inline.

## Phase 12: requirements check — done 2026-11-19

- New agent `requirements-check` (sonnet, read-only), two modes. `plan`: extracts the requirements (R1..Rn) itself from the ticket files and the interview answers, never from the planner's "Key Requirements Extracted", and maps each to the plan: covered, partial, missing, contradicts, blocked, plus Ambiguous readings and Extras (scope the BRD does not ask for). `implementation`: checks each R-ID against the diff since BASE: met, partial, not met, runtime only, plus Regressions.
- create-plan 7b spawns it first; its table replaces the old Coverage Matrix as `## Requirements (BRD)` in VERIFICATION.md (which gains `Plan:` and `Sources:` lines). Confirmed missing/contradicts = critical, partial or an unexplained Extra = warning, Ambiguous and kept Extras = questions in Step 8 (with `--auto` through AskUserQuestion). Each regeneration re-runs it.
- implement-plan `<finish>` step 1 spawns it in implementation mode while validate-plan runs, finds VERIFICATION.md by its `Plan:` line in `thoughts/groom/` or `history/` (plan-archive moves it), fixes confirmed gaps with the validation fixes, appends `## Implementation Check`, summary gains a Requirements line. Plans from before this change have no requirements table: the check is skipped and said so.
- Untested: first real run of both modes.

## Phase 13: Opus advisor for Sonnet sessions — 2026-11-19

- `hooks/register.ts` (a mod module, named by `hooks/hooks.json`): a `settings.read` hook. On the merged read with no `advisorModel` set, a main model that is not Opus, Fable or Mythos gets `advisorModel: "opus"`; Opus sessions are left alone (the advisor must be at least as capable as the executor). A user-set `advisorModel` always wins. A failing hook falls back to the engine's settings (`.catch`).
- Why a hook: Claude Code has no per-command or per-skill advisor (no frontmatter key), only the `advisorModel` setting and `/advisor`.
- Limit: the engine re-merges settings only when settings or plugins change, so the model at the last merge decides. A `/model` switch, or orchestrate's `set_session_model` right after `start_session`, may not re-trigger it; `/reload-plugins` does. Changing the advisor model itself applies after `/clear` or `/compact`.
- Untested: whether a Sonnet session really shows the advisor tool, and whether orchestrate's stage sessions pick it up.

## Still open

- First real `/vad4nus:orchestrate` run in a fresh session: does `start_session` share the worktree and take a slash command as the first message, do turn-end notices arrive, does each marker show up in `list_events`.

- First real `/vad4nus:create-plan` run: watch Step 0, the Step 5 question, and the Step 7c Codex review end to end.
- First real `/vad4nus:ios-run staging-next` run (an iOS build, so only when asked), and one with `--real` (added 2026-10-14: `devicectl` lists connected devices, build with `-allowProvisioningUpdates`, install and launch through `devicectl`, a process check instead of a screenshot).
- First real `/vad4nus:implement-plan` run with `<finish>`: check that validate-plan is read from the sibling file, the review agent gets the rubric path, and the fix loops stay bounded.
- First real `/vad4nus:ios-testflight` run. Untested: prod through the CLI, a build number other than 1 (the notification extension hardcodes `CFBundleVersion` 1), and re-uploading an existing version and build.
- Jira Cloud: add `fetch-cloud-jira-tasks` as a separate commit once Server is proven.
- Jira Server fetch: the mid-download interruption check (previous folder survives) is not exercised yet.
