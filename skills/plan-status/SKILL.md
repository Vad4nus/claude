---
description: "Report the current grooming/planning session status: interview, research, plan, and verification artifacts"
model: claude-haiku-4-5
disable-model-invocation: true
---

# Plan Status

Report the state of the current planning session. **Read-only** — never modify any file.

## Language Rule

The summary you print to the user mirrors the language of the user's request (the example below is Russian). The artifacts themselves stay in English; do not translate their contents, only describe them.

## Process

1. **Inspect `thoughts/groom/`** and report which session artifacts exist:
   - `TASK.md` — interview answers + extracted requirements
   - `CONTEXT.md` — research digest
   - `VERIFICATION.md` — plan-quality verdict (read and report the PASS/FLAG/FAIL line and counts)

2. **Locate the active plan** in `thoughts/shared/plans/`. Report the path of the most recent plan and its phase headings.

3. **Report progress if available.** If `/vad4nus:implement-plan` has been run, surface the next pending task and the files it will touch (read the plan's unchecked success criteria). Do not invent progress state that does not exist.

4. **If `thoughts/groom/` is empty or missing**, report that there is no active grooming session and suggest `/vad4nus:create-plan`.

## Output Format

Print a concise summary in the user's language, for example (Russian):

```
Сессия груминга:
- TASK.md: есть (требований: 4)
- CONTEXT.md: есть
- VERIFICATION.md: вердикт PASS (criticals: 0, warnings: 0)
- План: thoughts/shared/plans/2026-06-03-add-user-search.md (фаз: 3)
- Следующая задача: Phase 2 — ... (файлы: src/...)
```
