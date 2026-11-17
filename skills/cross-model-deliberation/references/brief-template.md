# Codex brief templates

Two briefs are used: the initial independent consult (step 4) and the optional rebuttal
(step 6). Both are forwarded through `codex:codex-rescue` as the task text after the
`--wait --fresh --model gpt-6-astra --effort max` prefix. Plan review mode replaces the initial
consult with the "Plan review" brief at the end of this file and passes the caller's effort.

## Transport rules

The brief becomes a shell argument inside the wrapper's `Bash` call. Therefore:

- Keep it ASCII-safe. Avoid backticks, `$`, and nested quote characters, which can be mangled or
  expanded in transit. Name identifiers in plain prose instead of fencing them.
- Do not paste large files. Codex runs inside the repository with read access under the read-only
  sandbox, so give it paths and line ranges and let it read for itself.
- Keep the whole brief under roughly 400 words. Evidence lives in the repo, not in the argument.

## Initial consult

The first line is mandatory and verbatim. It is what makes the rescue wrapper omit `--write`,
which the companion maps to a read-only sandbox request: the wrapper adds `--write` by default
and omits it only when the request clearly reads as review, diagnosis, or research without
edits. Nothing else in the flags requests read-only.

```text
READ-ONLY CONSULTATION - review and diagnosis only, no edits. Do not pass --write.

Decision: <one sentence stating the choice or diagnosis to be settled>

Context: <2-4 sentences. System, constraints, what has already been ruled out and why>

Evidence to read: <repo-relative paths, line ranges, test or log names>

Options under consideration: <name each option neutrally, no preference expressed>

Return, in this order:
1. Options you consider viable, including any this brief did not list
2. Your recommendation and the reasoning that drives it
3. Assumptions you are relying on
4. Supporting evidence, cited by file and line
5. Failure modes of your own recommendation
6. Evidence that is missing and would change your answer
7. Confidence, low, medium, or high, with the reason
```

Do not include Claude's recommendation, ranking, or leaning anywhere in this brief. Anchoring
Codex defeats the purpose of the consult.

## Rebuttal consult

Use only when a disagreement could actually change the decision. Anchoring is acceptable here,
because the goal is adversarial pressure on a specific disputed point.

```text
READ-ONLY CONSULTATION - review and diagnosis only, no edits. Do not pass --write.

Two independent analyses of the same decision disagree. Challenge both.

Analysis A: <Claude's memo, condensed>

Analysis B: <Codex's prior memo, condensed>

Disputed point: <the single assumption or claim that decides the outcome>

Return:
1. Which assumption, if any, is unsupported by the evidence, cited by file and line
2. The strongest case against each analysis
3. A concrete test, query, or measurement that would settle the dispute
4. Whether the disagreement is material to the decision or cosmetic
```

## Plan review

Used by Plan review mode instead of the initial consult. Same transport rules and the same
mandatory first line. Do not tell Codex which parts of the plan Claude is unsure about.

```text
READ-ONLY CONSULTATION - review and diagnosis only, no edits. Do not pass --write.

Review an implementation plan against this repository before it is approved.

Plan: <repo-relative path to the plan>
Requirements: thoughts/groom/TASK.md

Read the code yourself and check:
1. Requirements in TASK.md that no phase covers
2. File and line references that are wrong or stale
3. Phase order: a phase that needs something only a later phase creates
4. Changes the plan misses: callers, DI registration, platform counterparts, tests
5. Scope that the requirements do not ask for
6. Verification commands that do not exist or cannot prove their criterion

Return a numbered list. Each item: check number, plan section, the problem, evidence by file
and line, suggested fix. State plainly when a check found nothing. End with confidence, low,
medium, or high, and the reason.
```
