# Plan Template Reference

Load this file at Step 6 (writing the plan). It defines the required plan structure, the per-phase template, and how to write success criteria. The procedure, interview rules, and guardrails stay in `SKILL.md`.

## Required Plan Sections

The plan must include these sections:

- **Overview**: what and why
- **Current State Analysis**: what exists now, what's missing, key constraints
- **Desired End State**: target state and how to verify it
- **What We're NOT Doing**: explicit out-of-scope items
- **Implementation Approach**: high-level strategy and reasoning
- **Phase N: [Name]** (one per phase): use the per-phase template below
- **Testing Strategy**: unit, integration, manual testing steps
- **Performance Considerations**: implications or optimizations
- **Migration Notes**: how to handle existing data/systems (if applicable)
- **References**: original ticket, related research, similar implementations
- **Blocked** (only when a source was unavailable): one item per source with what failed and the exact error, what the user must fix, and which phases or sections wait on it. Each waiting spot in the plan holds a `BLOCKED: <source> — <what is missing>` placeholder, never guessed content.

## Per-Phase Template

```markdown
## Phase N: [Name]

**Priority:** P0 | P1 | P2 (P0 = blocking, P1 = core, P2 = polish)
**Risk:** low | medium | high (low = isolated, medium = shared code, high = migration / API contract)

### Read Before Starting

- `path/to/file.ts` — why it matters for this phase

### Changes Required

- `path/to/file.ts` — what changes

### Success Criteria

#### Automated Verification

- [ ] {measurable, command-backed}

#### Manual Verification

- [ ] {requires human}
```

**Read Before Starting** lets the execution agent (`/vad4nus:implement-plan`) load the right context per phase. Keep lists specific — concrete paths, never "read the codebase".

## Success Criteria Guidelines

Always split success criteria into two categories:

1. **Automated Verification** (run by execution agents): commands like `just test`, `npm run lint`; files that should exist; compilation/type checking; automated test suites.
2. **Manual Verification** (requires human): UI/UX functionality; performance under real conditions; edge cases hard to automate; user acceptance.

Acceptance criteria must be measurable and domain-appropriate:

- **UI component:** `[ ] When isLoading=true, <Spinner> renders instead of content`
- **API endpoint:** `[ ] POST /api/invoices with valid body returns 201 and { id, status: "draft" }`
- **DB migration:** `[ ] migrate up adds column invoices.due_date DATE NULL; migrate down removes it`
- **CLI command:** `[ ] foo build --dry-run exits 0 and prints the planned actions`

Reject non-criteria: "works correctly" (not measurable), "Component X renders" (too vague — render to what end state?).
