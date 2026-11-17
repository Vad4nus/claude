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

## VERIFICATION.md (Step 7b — write; Step 7c — append)

Record the plan-quality verdict.

```markdown
# VERIFICATION.md — Plan Quality Assessment

> **Task:** {slug}
> **Verdict:** **{PASS | FLAG | FAIL}**
> **Criticals:** {N} | **Warnings:** {N}

## Coverage Matrix

| #   | Requirement | Covered By | Status |
| --- | ----------- | ---------- | ------ |
| 1   | {text}      | Phase {N}  | YES    |

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
```
