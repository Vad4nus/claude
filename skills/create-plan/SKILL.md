---
description: "Create a detailed implementation plan through codebase research and interactive refinement. Args: <task text | ticket path>; --agents haiku|sonnet|opus sets the research agents' model; --codex-effort high|xhigh|max sets the Codex plan review effort (default xhigh); --no-codex skips that review; --auto skips the approval and iteration steps and ends with PLAN: <path> (for orchestrate). E.g. /vad4nus:create-plan --no-codex ~/Jira/jira.jetru.by/W30-891/ticket.md"
model: opus
effort: high
argument-hint: "[--agents haiku|sonnet|opus] [--codex-effort high|xhigh|max] [--no-codex] [--auto] <task | ticket path>"
disable-model-invocation: true
---

# Create Plan

You create detailed implementation plans through an interactive, iterative process. Be skeptical, thorough, and collaborative; don't assume — verify with code.

## Command Contract

How to invoke this command and what to expect.

### Flags

Parse these from the start of the arguments and strip them before applying the input table below:

| Flag                              | Default                   | Effect                                                        |
| --------------------------------- | ------------------------- | ------------------------------------------------------------- |
| `--agents <haiku\|sonnet\|opus>`  | each agent's own model    | Pass `model: <value>` on every research Agent call in Step 2  |
| `--codex-effort <high\|xhigh\|max>` | `xhigh`                 | Codex reasoning effort for the Step 7c review                 |
| `--no-codex`                      | off                       | Skip Step 7c                                                  |
| `--auto`                          | off                       | No Step 5 approval, no Step 8 iteration; ends with `PLAN: <path>` (used by orchestrate) |

An unknown flag or value: say so and ask whether to continue with the default. Never guess.

### Input

| Input                         | Interpretation             | Action                                                                          |
| ----------------------------- | -------------------------- | ------------------------------------------------------------------------------- |
| Existing file path            | Ticket or context document | Read the file fully, treat contents as the task description                     |
| Path to non-existent file     | Likely a typo              | Inform user the file was not found, ask if they meant to type a description     |
| Plain text (not a valid path) | Task description           | Use the text directly as the task description; do not attempt to open as a path |
| No arguments                  | Interactive mode           | Prompt the user to provide the task description                                 |

Heuristic for plain text vs path: if the argument contains line breaks, natural-language verbs (add, fix, refactor, update, implement), or exceeds 200 characters, treat it as a task description immediately without checking the filesystem.

Examples:

- `/vad4nus:create-plan thoughts/allison/tickets/eng_1234.md` — reads the ticket file
- `/vad4nus:create-plan add rate limiting to the API gateway` — uses the text as task description
- `/vad4nus:create-plan` — enters interactive mode, asks the user for details
- `/vad4nus:create-plan --agents opus --codex-effort max migrate auth tokens to keychain` — stronger research agents and a max-effort Codex review
- `/vad4nus:create-plan --no-codex fix the typo in the settings title` — no Codex review

## Conventions

These rules apply throughout the whole process.

### Language Rule

- **User-facing text** — every chat message, `AskUserQuestion` prompt, header, and option label mirrors the language of the user's request. The Russian wording shown in this document ("Продолжить", "Достаточно", etc.) is an example for a Russian-speaking user — render the equivalent in the user's language and apply the same choice logic.
- **Artifacts** — every file you write (TASK.md, CONTEXT.md, the plan, VERIFICATION.md) is written in **English only**. Translate the user's answers to English when persisting them.
- **Preserve the original task description verbatim** in whatever language the user provided it.

### Session Artifacts (fixed paths)

| Artifact             | Path                                         | Purpose                                                         |
| -------------------- | -------------------------------------------- | --------------------------------------------------------------- |
| Interview record     | `thoughts/groom/TASK.md`                     | Original description, interview answers, extracted requirements |
| Research digest      | `thoughts/groom/CONTEXT.md`                  | Short summary of Step 2 findings (optional)                     |
| Plan-quality verdict | `thoughts/groom/VERIFICATION.md`             | Coverage matrix + PASS/FLAG/FAIL                                |
| The plan             | `thoughts/shared/plans/YYYY-MM-DD-<slug>.md` | The permanent deliverable                                       |

The `thoughts/groom/` artifacts are ephemeral session state; the plan in `thoughts/shared/plans/` is the permanent deliverable. Inspect with `/vad4nus:plan-status`, clear with `/vad4nus:plan-archive`.

### Interview Termination

There is **no fixed question limit**. The interview (pre-research in Step 1.5, deep in Step 3) ends when **either**:

1. **No open questions remain** — nothing genuinely unresolved that the user or the code couldn't already settle. Then stop **without** showing the "Продолжить / Достаточно" prompt.
2. **The user chooses "Достаточно"** at a continue/stop prompt.

To keep the interview convergent:

- **Only ask genuinely open questions.** Never ask anything already answered, already in the task description, or resolvable by reading the code — drop such candidates.
- **Only ask about the task itself** — its scope, behavior, constraints, edge cases. Never ask about workflow mechanics the user didn't raise (which branch to use, how to commit, who reviews, deployment process) — those are out of scope for planning; use the project's current state as-is.
- **Maintain an explicit open-questions list** (the `## Open Questions` section of `TASK.md`). Each batch draws only from it; every answer removes the question it resolved. The list must shrink each round.
- **If a batch opens no new questions and the list is empty, stop** — do not prompt or invent filler.
- **Convergence guard:** if a round doesn't reduce the open-questions count, don't silently re-ask. Rephrase once for the same gap, or note it under `## Open Questions` and move on. Never loop on the same point more than twice.

### Guardrails

Planning is a read-and-write-artifacts activity. It must not touch the project or its history.

- **Read-only git** — never `commit`, `push`, `branch`, `checkout`, `reset`, `stash`, or `tag`. Read history (`log`, `blame`) only.
- **Writes confined** — write only under `thoughts/groom/` and `thoughts/shared/plans/`. Never modify project source while planning.
- **Honest failure** — if a step can't complete (agent fails, file missing, command unresolved), say so explicitly. Never fabricate findings, paths, or test commands.
- **Unavailable source → blocked, never guessed** — a source the plan needs is unavailable: an MCP server not connected or not authorized (Figma, Jira), a ticket, attachment or design that cannot be fetched, missing access or a missing file. Never fill the gap with assumptions about what it would say. Tell the user right away, in one line, what does not work, the exact error and what to fix (e.g. authorize Figma via `/mcp`). Continue with everything that does not depend on it. In the plan, the dependent part becomes a `BLOCKED: <source> — <what is missing>` placeholder and is listed under `## Blocked` (see [plan-template.md](plan-template.md)). Once the user fixes it, fill only the blocked parts.
- **No destructive shell** — no `rm -rf`, force-push, database drops, or `kill -9`. Any test command must be safe and bounded (under ~30s); otherwise report it without running.

## Process Steps

Execution is a single sequential order. Do not skip ahead or run research before understanding the input.

### Step 0: Refresh the Code Index

Call the codebase-memory-mcp `index_repository` tool with `repo_path` set to the output of `git rev-parse --show-toplevel`. It is incremental: under a second when warm, a few seconds cold (a fresh worktree is always cold). If the tool is unavailable or fails, say so in one line and continue; the graph speeds research up but is not required.

### Step 1: Read and Understand the Input

1. **Read user-provided files immediately and fully** (tickets, research docs, related plans, referenced JSON/data). Use Read WITHOUT limit/offset — NEVER read user-provided files partially.
2. **Form an initial understanding** of task scope, constraints, and context.

If no argument was provided, respond with: "What are we building? Provide a task description, ticket path, or paste the ticket text." Then wait for input.

### Step 1.5: Pre-Research Interview (Light)

Before touching the code, uncover hidden requirements the description doesn't state. Keep this short — its purpose is to aim the research, not to plan.

1. **Ask a focused batch** of **2–4 questions** in a single `AskUserQuestion` call (user's language), drawing from this menu (pick what's actually unknown, not a checklist):
   - Business value & goals — why this, what outcome
   - Scope & boundaries — what's explicitly in / out
   - Technical constraints — must-use or must-avoid
   - Edge cases & risks — what could go wrong

   Each question answerable in 1–2 sentences. Header form `"В{N}: {категория}"` (localize to the user's language).

2. **After each batch**, while open questions remain, make a separate `AskUserQuestion` call (never mixed with content questions):

   ```
   header:   "Интервью — задано вопросов: {N}"
   question: "Продолжить задавать вопросы или достаточно?"
   options:  ["Продолжить", "Достаточно"]
   ```

   **Продолжить** → another batch (from remaining open questions); **Достаточно** → stop. If no open questions remain, **don't show this prompt** — stop. Follow **Conventions → Interview Termination**.

3. **Persist** answers (translated to English) to `thoughts/groom/TASK.md` — use the TASK.md format in [artifacts.md](artifacts.md).

### Step 1.6: History Context Check

Past grooming sessions are archived to `thoughts/groom/history/YYYY-MM-DD-<slug>/` by `/vad4nus:plan-archive`. Reuse that knowledge instead of re-researching.

1. **Skip** if `thoughts/groom/history/` is missing or empty.
2. **Scan** each `history/*/CONTEXT.md`; extract its scope and relevant files.
3. **Score overlap** against task tokens from `TASK.md`: **+2** per matching relevant-file, **+1** per scope-word match. Surface a candidate when score is **≥ 2** or it has **≥ 1 file match**.
4. **If a candidate is found**, ask via `AskUserQuestion` (user's language):

   ```
   header:   "Найден похожий прошлый контекст"
   question: "Использовать архивный CONTEXT.md от {date} ({slug})?"
   options:  ["Использовать повторно", "Взять за основу", "Игнорировать"]
   ```

   - **Использовать повторно** → _reuse_: copy that `CONTEXT.md` to `thoughts/groom/CONTEXT.md` and **skip Step 2**.
   - **Взять за основу** → _baseline_: copy it, then **still run Step 2** to verify entries are current and extend in place.
   - **Игнорировать** → _fresh_: ignore history, run full research.

5. If no candidate clears the threshold, proceed to Step 2 as a fresh run.

### Step 2: Research the Codebase (After Understanding the Input)

Only after reading/understanding the input and running the pre-research interview.

Honor the Step 1.6 decision: **reuse** → skip this step; **baseline** → verify and extend the copied CONTEXT.md; **fresh** → full research below.

Feed the **Key Requirements Extracted** from `TASK.md` into agent prompts so research aims at what the user cares about.

1. **Spawn parallel research agents** in three batches; each batch completes before the next. Provide each agent detailed instructions (what to search, which dirs, what to extract, expected output) and request specific `file:line` references. If `--agents` was given, pass its value as `model` on every Agent call.

   **Batch 1 — Context (understand what's requested):**
   | Agent | When to use | Expected result |
   | ----------------- | --------------------------------------------- | -------------------------------------------------------------------- |
   | vad4nus:thoughts-locator | Find existing research, plans, or decisions | Paths to relevant thoughts documents |
   | vad4nus:thoughts-analyzer | Extract key insights from specific documents | Summary of decisions, patterns, constraints with document references |

   **Batch 2 — Code (understand how it works now):**
   | Agent | When to use | Expected result |
   | ----------------------- | --------------------------------------------------- | ------------------------------------------------------------------------ |
   | vad4nus:codebase-locator | Find files related to a feature, component, concept | List of relevant file paths with brief role descriptions |
   | vad4nus:codebase-analyzer | Understand how an existing implementation works | Detailed explanation with file:line references, data flow, key functions |
   | vad4nus:codebase-pattern-finder | Find similar features or patterns to model after | Files and approaches used in analogous implementations |

   **Batch 3 — Validate (prior attempts and external context):**
   | Agent | When to use | Expected result |
   | -------------------- | --------------------------------------------------- | -------------------------------------------------- |
   | vad4nus:web-search-researcher | Find similar implementations, prior art, known issues | Links and summaries of relevant external solutions |

2. **Wait for ALL agents in a batch** before proceeding. Cross-check results against the actual codebase; spawn follow-ups if results seem incorrect.

3. **Prioritize and read found files**: user-provided input (read fully, done in Step 1); key files central to the implementation (read fully); large auxiliary files (read selectively — relevant sections only). Do NOT blindly read every found file in full.

4. **Analyze and verify understanding**: cross-reference requirements with code, identify discrepancies/misunderstandings, note assumptions to verify, determine true scope from codebase reality.

5. **Resolve test and lint commands via a ladder** (first match wins) — never invent them:
   - Gradle (`gradlew` at the repo root): per-module targeted tasks, the same set `vad4nus:kmp-verify` picks: `:<module>:testDebugUnitTest` for `shared`/`domain`/`data`, `:androidApp:compileDevDebugKotlin`, root `detekt`, `generateMR` after resource edits. Name the tasks the phase actually touches. Never a bare `./gradlew test`: it builds every flavor and runs out of memory here.
   - Test: `package.json` → `scripts.test`; else by manifest (`Cargo.toml`→`cargo test`, `go.mod`→`go test ./...`, `Gemfile`→`bundle exec rspec`, `pyproject.toml`/`setup.py`→`pytest`, `mix.exs`→`mix test`); else `Makefile` `test` target; else record "test command unknown — check project docs".
   - Lint: `package.json` → `scripts.lint`; else by manifest (`cargo clippy`, `go vet ./...`, `bundle exec rubocop`, `ruff check .`/`flake8`); else `Makefile` `lint`; else "lint command unknown".

6. **No-results fallback** — if research surfaces no similar features or relevant code, do **not** proceed with an empty picture. Document the project foundations instead: stack & versions (from manifests), how a new module/feature is conventionally started, the architecture pattern, naming conventions, test setup, an entry-point map. Mark this clearly so the plan rests on foundations, not non-existent precedent.

7. **Optionally write a short research digest** to `thoughts/groom/CONTEXT.md` (English): existing patterns found (with paths), relevant files and read priority, the resolved test/lint commands, and constraints. Keep it to what informs the plan.

### Step 3: Present Understanding and Deep Interview

1. **Present your informed understanding**: (1) accurate task summary, (2) key findings with `file:line` references.
2. **Run the deep interview** — now that the code is understood, ask what code investigation could _not_ resolve (testing & validation expectations, remaining edge cases, acceptance criteria). Same mechanics as Step 1.5 — see **Conventions → Interview Termination**. Carry over unresolved items from Step 1.5's `## Open Questions`. Never ask what the code already answers.
3. **Append** these answers to the existing `thoughts/groom/TASK.md` (do not overwrite pre-research answers).

### Step 4: Handle Corrections

If the user corrects a misunderstanding: do NOT accept at face value. Spawn new research to verify, read the specific files/dirs they mention, and only proceed once you've verified the facts yourself.

### Step 5: Propose Plan Structure

Once aligned on the approach, show the structure in chat (user's language):

```
## Overview
[1-2 sentence summary]

## Implementation Phases:
1. [Phase name] - [what it accomplishes]
2. [Phase name] - [what it accomplishes]
3. [Phase name] - [what it accomplishes]
```

Then get approval through `AskUserQuestion`, never a plain-text question. A plain-text question ends the turn, and the next turn drops this skill's pinned model; `AskUserQuestion` keeps one turn running through Step 7c.

```
header:   "Структура плана"
question: "Структура подходит?"
options:  ["Утвердить", "Поправить"]
```

With `--auto`: show the structure, skip the question, go to Step 6.

**Утвердить** → Step 6. **Поправить** (or a free-text answer) → apply the correction, show the updated structure, ask again. Same convergence guard as the interview: never more than twice on the same point.

### Step 6: Write the Plan

After structure approval, write the plan to `thoughts/shared/plans/YYYY-MM-DD-ENG-XXXX-description.md`:

- `YYYY-MM-DD` = today's date; `ENG-XXXX` = ticket number (omit if none); `description` = kebab-case.
- Examples: `2025-01-08-ENG-1478-parent-child-tracking.md`, `2025-01-08-improve-error-handling.md`.

Load [plan-template.md](plan-template.md) and follow it for the required sections, the per-phase template, and the success-criteria guidelines.

### Step 7: Pre-Save Guardrails, Plan-Quality Verification, Codex Review

#### 7a. Pre-Save Guardrails

Self-check before finalizing; fix any failure before proceeding:

- [ ] All open questions resolved — none remain in the plan (parts waiting on an unavailable source are not questions: they sit under `## Blocked`)
- [ ] Nothing guessed for an unavailable source — every such gap is a `BLOCKED:` placeholder listed under `## Blocked`
- [ ] Specific `file:line` references present wherever promised
- [ ] No invented test commands — every referenced command actually exists in the project
- [ ] Explicit out-of-scope block ("What We're NOT Doing") present and specific
- [ ] Automated and manual verification checks clearly separated
- [ ] Target directory exists (`thoughts/shared/plans/`)
- [ ] Not overwriting an existing plan without the user's confirmation

#### 7b. Plan-Quality Verification

Audit the plan **mechanically** against requirements before presenting. This checks the _quality of the plan_ (distinct from `/vad4nus:validate-plan`, which checks _execution_ after coding). Run these binary (YES/NO) checks:

**Criticals** (each NO is a critical):

- Coverage — every requirement in `TASK.md` is covered by ≥1 phase/task. A `BLOCKED:` placeholder counts as covered; list it in `VERIFICATION.md`.
- Atomicity — no task touches >3 files, has >5 acceptance criteria, or mixes unrelated concerns.
- Dependency order — the task dependency graph is acyclic; every "read before" / "files to modify" target already exists or is created by an earlier task.

**Warnings** (each NO is a warning):

- File scope — all referenced paths are specific (no vague "the codebase"); modify/read targets exist (confirm with `ls`).
- Edge cases — edge cases captured in TASK.md are addressed in ≥1 task's acceptance criteria.
- AC quality — every acceptance criterion is measurable and domain-appropriate.
- Phase metadata — every phase sets Priority and Risk and has a specific "Read Before Starting" list.

**Verdict:**

| Verdict  | Condition                    | Action                                               |
| -------- | ---------------------------- | ---------------------------------------------------- |
| **PASS** | 0 criticals AND 0 warnings   | Plan ready to present                                |
| **FLAG** | 0 criticals AND 1–2 warnings | Present, but surface the warnings to the user        |
| **FAIL** | ≥1 critical OR ≥3 warnings   | Regenerate the plan (fix the gaps) before presenting |

**Regeneration is bounded.** On FAIL, fix the specific gaps and re-verify **at most twice**. If still FAIL after the second regeneration, stop: present the plan with the outstanding flags from `VERIFICATION.md` and ask the user how to proceed. Do not loop indefinitely.

Write the result to `thoughts/groom/VERIFICATION.md` (English) — use the VERIFICATION.md format in [artifacts.md](artifacts.md). Do not present the plan as final until the verdict is PASS or FLAG.

#### 7c. Codex Review of the Draft

Skip on `--no-codex`, and record `Status: skipped (--no-codex)` in the `## Codex Review` section of `VERIFICATION.md`.

Run only once 7b is PASS or FLAG. Load the `vad4nus:cross-model-deliberation` skill and follow its **Plan review mode** with the plan path, `thoughts/groom/TASK.md`, and effort = the `--codex-effort` value (default `xhigh`).

Handle each Codex finding:

- **Confirmed against the code** → fix the plan, then re-run the 7b checks the fix touches.
- **Rejected** → keep it, with the evidence for rejecting it.
- **Changes scope or approach** → do not settle it alone; carry it into Step 8 as a question for the user.

Append the `## Codex Review` section to `VERIFICATION.md` (format in [artifacts.md](artifacts.md)). If the consult errors, times out or comes back empty, say so, record `Status: unavailable: <reason>`, and continue. Never call such a plan Codex-reviewed.

### Step 8: Review and Iterate

1. Verify the plan was saved to the correct path.
   If `## Blocked` is not empty, open with it: "Не работает: <source> (<error>). Поправь <what to fix>, и я закончу план: <blocked parts>" (in the user's language). When it is fixed, fill only those parts and re-run the 7a/7b checks they touch.
2. Present the path, the 7b verdict, and the Codex review outcome (what was fixed, what was rejected, open disagreements as explicit questions). Ask for feedback: phases, success criteria, technical details, missing edge cases.
3. Iterate — adjust phases, approach, success criteria, or scope — until the user is satisfied.
4. Once approved, tell the user they can inspect the session with `/vad4nus:plan-status` and archive it with `/vad4nus:plan-archive`. Implementation starts only by hand; give both ready-to-copy options:
   - `/vad4nus:implement-plan <plan path>` — continue in this session
   - `/clear`, then `/vad4nus:implement-plan <plan path>` — start from a clean context; the plan on disk carries everything, and after a long planning session this is the better choice

With `--auto`: after item 1, ask the open Codex disagreements through `AskUserQuestion` and apply the answers to the plan. Skip items 2 to 4. The very last line of the turn is `PLAN: <plan path>`.

## Plan Template Reference

The required plan structure, the per-phase template, and the success-criteria guidelines live in [plan-template.md](plan-template.md). Load that file at Step 6, before writing the plan.

## Important Guidelines

- **Be skeptical & interactive** — question vague requirements, get buy-in at each major step, allow course corrections; don't write the full plan in one shot.
- **Be thorough (minimum bar)** — read every user-provided file fully; spawn the three research batches (context + code + prior art); verify ≥2 `file:line` references per phase; never present a plan with unresolved questions (if one arises, STOP and research or ask). An unavailable source is not a question to settle by guessing: block that part (see Guardrails).
- **Be practical** — incremental testable changes; consider migration/rollback; think about edge cases and "what we're NOT doing".
- **Track progress** with TodoWrite as you complete research and planning tasks.
- **Code style** — NEVER use comments in code examples (except class docstrings) or emojis anywhere; code should be self-documenting through clear naming.
