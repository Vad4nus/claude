---
description: "Run the whole cycle through side sessions, one per command: /vad4nus:create-plan --auto (research, interview, plan review), then /vad4nus:implement-plan (implementation, validation, fixes, code quality review), then /vad4nus:ios-run, then /vad4nus:ios-qa (a short hands-on check of the app on the simulator). Each side session gets its command's own model and a clean context; their questions are answered in them. Needs the Desktop start_session tool (a fresh session). Args: <staging|staging-next|dev|prod> is required (the ios-run flavor; may be omitted only with --no-ios); --no-ios skips the iOS run and the check; --no-testing skips only the check; --night asks every question up front, then the run goes on alone: agents take minor decisions, important ones are listed in the final report and hold back the check; --real and --device <name|udid> go to ios-run; --agents, --codex-effort, --no-codex go to create-plan; the rest is the task text or a ticket path. E.g. /vad4nus:orchestrate staging-next ~/Jira/jira.jetru.by/W30-891/ticket.md"
argument-hint: "<staging|staging-next|dev|prod> [--no-ios] [--no-testing] [--night] [--real] [--device <name|udid>] [--agents haiku|sonnet|opus] [--codex-effort high|xhigh|max] [--no-codex] <task | ticket path>"
model: sonnet
effort: medium
disable-model-invocation: true
---

# Orchestrate

A dispatcher. It runs the real commands, each in its own side session, one after another, and never does a stage's work itself.

## Stage 0: Arguments and preconditions, before anything else

- **Flavor** is the first argument: `staging`, `staging-next`, `dev` or `prod`. Missing or unknown, and no `--no-ios` → stop now with the argument hint and the example. Do not ask, do not guess.
- `--no-ios` → no flavor needed, Stages 3 and 4 are skipped.
- `--no-testing` → Stage 4 is skipped. `--real` skips it too: the iOS Simulator tools cannot drive a real iPhone.
- `--night` → the night run below.
- `--real`, `--device <x>` → kept for Stage 3. `--agents`, `--codex-effort`, `--no-codex` → kept for Stage 1. The rest is the task. No task → stop with the argument hint.
- The Desktop `start_session` tool must be available (look it up with ToolSearch if it is deferred). Not available → stop: "Не работает: нет инструмента start_session в этой сессии. Запусти команду в свежей сессии Desktop." Never fall back to running the stages here.
- Unless `--no-ios`: check the scheme now, so the run cannot fail hours later. Map the flavor with the table in `../ios-run/SKILL.md` (relative to this skill's base directory), then `(cd "$ROOT/iosApp" && xcodegen generate --quiet) && xcodebuild -list -project "$ROOT/iosApp/Watchlink.xcodeproj"` with the Bash sandbox disabled. Scheme not listed → stop with the reason ios-run gives in its step 3.

## Stage sessions

| Stage | Command and arguments | Model, effort | Done marker |
| --- | --- | --- | --- |
| 1. Plan | `/vad4nus:create-plan --auto <create-plan flags> <task>` | its own pin | `PLAN: <path>` |
| 2. Implement | `/vad4nus:implement-plan <path from stage 1>`, plus unless `--no-ios` the note `skip the closing iOS build question, ios-run follows in another session` | `sonnet`, `high` | `IMPLEMENT-PLAN DONE` |
| 3. iOS (unless `--no-ios`) | `/vad4nus:ios-run <flavor> <--real / --device>` | `sonnet`, `medium` | `IOS-RUN DONE` |
| 4. Testing (unless skipped) | `/vad4nus:ios-qa <flavor> --device <UDID from stage 3's report> <plan path>`, plus `Manual checks from implement-plan:` and that list from stage 2's summary | `sonnet`, `medium` | `IOS-QA DONE` |

The app opens sessions only in a turn that started with the user's own message; a turn started by a session's turn-end note gets "Start sessions only on the user's own words" and a card to click. So every stage session is opened in the first turn, and later stages are started by a message.

## First turn: open all stage sessions

1. Plan session: `start_session` with `initiation: "user_asked"`, `context: "fresh"`, `use_worktree: false` (this session's folder), `wake_when_done: true`, `prompt` = the stage 1 command line. A slash command as the first message runs as a real command with its own model pin.
2. Implement session, the iOS session unless `--no-ios`, and the testing session unless Stage 4 is skipped: the same, with `prompt` = `Stage <N> of orchestrate. Nothing to do yet: reply with one line «Жду старт от orchestrate» and end the turn. The orchestrate session will send a message starting with GO; then do exactly what it says.` Right after, `set_session_model` and `set_session_effort` on it from the table. The model takes the picker's id: `sonnet` is refused with the list of ids, so pass the Sonnet one from that list (`claude-sonnet-5-5` today). A cross-session message is plain text, never a slash command, so these sessions follow the command's SKILL.md file instead (step GO below); setting the model here keeps the command's own model. If the app asks to approve the change, that happens now, while the user is here.
3. `mcp__ccd_window__open_session_in` with `target: "split"` for the plan session.
4. With `--night`: the night pre-flight below first.
5. One line: the plan runs in [its title](#<session_id>), questions are answered there, the rest starts by itself (with `--night`: «напишу, когда можно уходить»). End the turn.

## Each turn-end note

Read the noted session's last messages with `list_events`.

- The stage's done marker is there → **GO** the next stage: `SendMessage` to its session id with `GO: read <this skill's base directory>/../<command>/SKILL.md in full and follow it exactly, as if the user had invoked /vad4nus:<command> <arguments>. Its base directory is <this skill's base directory>/../<command>.`, and for stage 3 also ` Implement session for build fixes: <stage 2 session id>.` Then `open_session_in` `split` for it and one line to the user. The last stage's marker → the final report. Stage 3's report says the app did not launch → no Stage 4 GO, the final report.
- No marker (a waiting session's first reply, a question to the user, a background build, a failure it reported) → one short line, wait again. Never GO a stage twice on your own. With `--night`, a question goes by the night rules below.
- Build-fix loop: a failed iOS build goes straight from the iOS session to the implement session (`BUILD-FAILED`), which fixes it and answers `BUILD-FIXED`; the iOS session then rebuilds (ios-run step 5a, up to 5 rounds). Those turn-end notes get one short line each ("сборка упала, implement чинит, раунд n" / "исправлено, iOS пересобирает"); never relay, never GO.
- The user says to continue here after fixing a failure → send that stage's GO again. The user says stop → the final report.

## Night run (`--night`)

The user answers everything while the plan is made, then leaves; nobody answers after that. Anything that would wait for the user stalls the run until morning, so it is settled now.

**Pre-flight, in the first turn:**

1. Permission prompts: `get_session` on each side session. `permissionMode` not `auto` or `bypassPermissions` → `set_session_permission_mode` `auto` on it; the user approves the cards now. New sessions here start in `default`, where the first unapproved command would wait all night.
2. `mcp__ccd_settings__get_settings`: `keep_awake_while_working` off → `set_setting` it on (and `keep_awake_on_battery` if the Mac may run on battery).
3. Free disk: `df -g "$ROOT" | awk 'NR==2{print $4}'`. Under 20 GB → a question below: clean up now or go on (the 2026-10-20 run died on ENOSPC).
4. One `AskUserQuestion` with what the later stages otherwise stop on:
   - May the implement session build the iOS framework or run iOS tests mid-phase when the plan needs it (fresh `DIHelper.h` names, a UIKit measurement)? No → those parts wait for the user.
   - The change touches logic duplicated in Android and iOS (AGENTS.md KMP-first): extract it to KMP, or leave it and list it?
   - With `--real`: list the connected iPhones as ios-run step 1 does; more than one → which (its UDID goes to Stage 3 as `--device`).
   - The disk question from step 3, if any.

The plan session asks its own questions (interview, Codex disagreements) before printing its marker. So on `PLAN:`, before the Stage 2 GO: «Вопросов больше нет, можно уходить. Крышку ноутбука не закрывай. Итог будет здесь.»

**Night note**, appended to every GO, the answers filled in:

`NIGHT RUN: the user has left until this pipeline ends, nobody will answer. This overrides every instruction to ask the user or wait for them (AskUserQuestion, mismatch reports, "ask first"): never call AskUserQuestion, never end the turn on a question. Minor decision (naming, file placement within the conventions, one of two equivalent implementations, test layout, a plan step the code already satisfies) → take the safe default and go on. Important decision (user-visible behavior or UI the plan does not fix, an API or data contract, work beyond the plan's scope, Android and iOS disagreeing on which is right, anything hard to undo) → do not guess: leave undone only what depends on it, finish the rest. The final message lists, before the done marker, «Decided at night» (one line per minor decision) and «Questions for the user» (per question: the options, your recommendation, what waits on it; «none» if none). Deferred parts count as blocked: still end with the done marker. The user's answers before leaving: <answers>.`

**Turn-end notes at night:**

- A stage ends its turn on a question anyway (no marker, not a build wait) → `SendMessage` it once: `NIGHT RUN: nobody will answer. Apply the night rules from your GO message: decide or defer, then go on and finish with your done marker.` It asks again → its question goes to the report, and the final report now.
- Stage 2 or 3 lists any «Questions for the user» → no Stage 4: QA waits for the answers. Stage 3 still runs.

**Final report at night** opens with «Вопросы к тебе»: every question from every stage with its options, the agent's recommendation, what waits on it, and a link to the session to answer in. Testing skipped for this reason → the command to run it after answering: `/vad4nus:ios-qa <flavor> --device <UDID> <plan path>`. After the usual sections: «Решено ночью», the minor decisions per stage.

## Final report

The last message, in the user's language, built from the side sessions' final messages (`list_events`), with a link to each session:

1. Plan: path, 7b verdict, Codex outcome.
2. Implementation: phases done, validation, review findings applied or left for the user, blocked parts with the resume command.
3. iOS: scheme, simulator or device, build time, fix rounds with what each fixed, launched yes or no; or "skipped (--no-ios)".
4. Testing: each check with its verdict, failures with steps and screenshot path; or skipped with the reason (`--no-testing`, `--real`, `--no-ios`, the app did not launch).
5. Manual checks: the full numbered list from implement-plan's summary, never a count; mark the ones ios-qa passed.
