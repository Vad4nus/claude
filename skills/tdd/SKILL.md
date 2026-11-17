---
description: "Enforce strict Test-Driven Development methodology: RED (failing test) -> GREEN (minimal impl) -> REFACTOR. Never write implementation without failing test first."
---

## Core Principle: Test-Driven Development (TDD)

**MANDATORY**: All code must be written using strict TDD methodology:

1. **RED**: Write a failing test first
2. **GREEN**: Write minimal code to pass the test
3. **REFACTOR**: Improve code while keeping tests green

### TDD Workflow Requirements

1. **Never write implementation code without a failing test**
2. **Each RED→GREEN cycle must take less than 5 minutes**
3. **Refactor after EVERY green test**
4. **Review code after each complete TDD cycle**

## Post Implementation Workflow

After writing code, run the linting command for code that's been changed. If there are linting errors fix them - do not just mark them as ignored.
If you run tests and some fail, you are also responsible for investigating and fixing them. All tests should pass. If tests fail, you're not done.

## Language Rule

Chat with the user in the user's language (mirror their request). Code, tests,
and commit messages stay in English.

## Final Response (mandatory)

End every TDD task with a chat message — after all tool calls — summarizing:
cycles completed (RED → GREEN → REFACTOR), files changed, the exact test and
lint commands run with their results, and anything still failing. Never end
the turn silently after running tests.
