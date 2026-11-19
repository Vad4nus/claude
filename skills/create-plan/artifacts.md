# Session Artifact Templates

Formats for the ephemeral `thoughts/groom/` artifacts. Load when you first write each file. All artifacts are English-only (see Conventions → Language Rule in `SKILL.md`).

## TASK.md (Step 1.5 — write; Step 3 — append)

Persist interview answers (translated to English). At Step 3, append the deep-interview answers; do not overwrite the pre-research ones.

```markdown
# TASK.md — Grooming Interview Answers

## Original Description

{raw description — verbatim, any language the user used}

## Interview Answers

### Q1 ({category}): {question in English}

**Answer:** {answer in English}

## Key Requirements Extracted

- {requirement in English}

## Open Questions

- {unanswered concern in English}
```

## VERIFICATION.md (Step 7b — write; Step 7c — append; implement-plan — append)

Record the requirements check and the plan-quality verdict. implement-plan finds this file by its `Plan:` line, also after `/vad4nus:plan-archive` moved it to `history/`, and checks the code against the `## Requirements (BRD)` IDs.

```markdown
# VERIFICATION.md — Plan Quality Assessment

> **Task:** {slug}
> **Plan:** {plan path}
> **Sources:** {ticket files, thoughts/groom/TASK.md}
> **Verdict:** **{PASS | FLAG | FAIL}**
> **Criticals:** {N} | **Warnings:** {N}

## Requirements (BRD)

The `requirements-check` agent's table, after your verdict on each finding (Note: `rejected: {evidence}`, `fixed: {plan change}`, `for user`).

| ID  | Requirement | Source                 | Plan                  | Status   | Note   |
| --- | ----------- | ---------------------- | --------------------- | -------- | ------ |
| R1  | {statement} | {file}: "{quote}"      | Phase {N}, {task}     | {status} | {note} |

### Ambiguous

- R{n}: {reading A} / {reading B}; the plan took {which}. {answer or for user}

### Extras

- Phase {N}, {task}: {what it changes}. {kept: why, or removed}

## Flags

### Critical

- {issue} — {recommendation}

### Warnings

- {issue} — {recommendation}

## Codex Review

> **Status:** {done | skipped (--no-codex) | unavailable: {reason}}
> **Effort:** {high | xhigh | max}

| #   | Finding | Verdict                                        | Plan change      |
| --- | ------- | ---------------------------------------------- | ---------------- |
| 1   | {text}  | {accepted \| rejected: {evidence} \| for user} | {change or none} |

## Implementation Check

> **BASE:** {commit} | **Checked:** {date}
> **Not met:** {N} | **Partial:** {N} | **Runtime only:** {N} | **Met:** {N}

| ID  | Status   | Evidence                        | Action                                                  |
| --- | -------- | ------------------------------- | ------------------------------------------------------- |
| R1  | {status} | {file:line, or what is missing} | {fixed: {change} \| for user: {why} \| manual: {check} \| none} |

### Regressions

- {file:line}: {requirement or non-goal it breaks}. {fixed or for user}
```
