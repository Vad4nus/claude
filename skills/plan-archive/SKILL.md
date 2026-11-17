---
description: "Archive the current grooming session artifacts to history and reset for the next task, preserving the plan"
model: claude-haiku-4-5
disable-model-invocation: true
---

# Plan Archive

Archive the current planning session and reset `thoughts/groom/` for the next task. The plan in `thoughts/shared/plans/` is a permanent deliverable and is **never** moved or deleted.

## Language Rule

User-facing prompts mirror the language of the user's request; the Russian wording in step 3 is an example — render the equivalent in the user's language. Artifact contents are not translated.

## Process

1. **Determine the session slug.** Derive it from `thoughts/groom/TASK.md` (the task description) or the most recent plan filename in `thoughts/shared/plans/`.

2. **Check that the plan is ready.** Look for a saved plan in `thoughts/shared/plans/` that matches this session's slug.
   - If a plan exists, the session is ready to archive — proceed.
   - If **no** plan exists yet, the grooming is unfinished. Warn the user explicitly in the confirmation prompt below (the interview/research artifacts would be archived without a finished plan) and only continue if they still confirm.

3. **Confirm first** via `AskUserQuestion` (user's language; Russian shown as example). Use the plan-ready wording when a plan was found, otherwise the no-plan warning wording:

   ```
   header:   "Архивировать сессию"
   question: "{Plan ready: 'План готов: <path>. Артефакты груминга будут перенесены в history, сессия очищена. План сохранится. Продолжить?'}
              {No plan:    'Внимание: готового плана в thoughts/shared/plans/ не найдено. Артефакты груминга будут перенесены в history без плана. Всё равно архивировать?'}"
   options:  ["Да, архивировать", "Отмена"]
   ```

   On **Отмена**, stop and change nothing.

4. **On confirmation, run the archive script** (it performs the move deterministically — correct date, atomic moves, collision suffix, never touches the plan):

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/skills/plan-archive/archive.sh" "<slug>"
   ```

   The script moves **every** item under `thoughts/groom/` (TASK.md, CONTEXT.md, VERIFICATION.md, and anything else) into `thoughts/groom/history/YYYY-MM-DD-<slug>/`, **except** `history/` itself — so the session is fully reset with nothing left behind. If the target dir already exists it appends a numeric suffix; if there are no artifacts it prints "nothing to archive" and changes nothing. It never touches `thoughts/shared/plans/`. Pass a second argument to override the groom directory if needed.

5. **Report** (user's language): relay what the script moved and where, and confirm the plan was preserved at its path. If the script exits non-zero (e.g. usage error), surface the error instead of claiming success.

## Guardrails

The filesystem mechanics live in `archive.sh` (move-only, collision-safe, preserves the plan and `history/`). The skill's responsibilities:

- **Always confirm before running the script** — archiving resets the session.
- **Run the bundled script**, do not hand-roll `mv`/`rm` commands — the script is the single source of truth for the move logic.
- **Never delete the plan** in `thoughts/shared/plans/` — the script does not touch it; neither should you.
- **Report honestly** — relay the script's actual output; if it reports "nothing to archive" or exits non-zero, do not claim a successful archive.
