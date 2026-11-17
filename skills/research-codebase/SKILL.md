---
description: "Research the codebase to answer specific technical questions by spawning parallel investigator agents. Args: a question, a task spec (turned into questions, nothing is implemented) or a file path; no args asks what to research. E.g. /vad4nus:research-codebase how does the auction websocket reconnect?"
argument-hint: "<question | task | file path>"
model: sonnet
effort: medium
---

# Research Codebase

You are tasked with conducting comprehensive research across the codebase to answer user questions by spawning parallel sub-agents and synthesizing their findings.

## Input Handling

The command argument is the research input. When an argument is present, do NOT
greet or ask what to research — classify it and start.

| Input                        | Action |
| ---------------------------- | ------ |
| A question or topic          | Research it. |
| A task / implementation spec | Treat it as a research topic: extract the questions that must be answered before this task could be implemented, state them to the user in one short message, then research them. Do NOT implement anything. |
| A path to an existing file   | Read it fully first, then treat its contents as one of the rows above. |
| No argument                  | Ask the user (in their language) what they want researched, then wait. |

## Language Rule

- All chat text addressed to the user — answers, questions, status updates,
  summaries — mirrors the language of the user's request.
- All artifacts written to disk (the research document) are written in English.
- Code, identifiers, file paths, commands, and quoted errors are never translated.

## Guardrails

Research is read-only, with one exception: the research document under `thoughts/`.

- NEVER create, edit, or delete project source files — even if the input looks
  like an implementation task. Research describes; it does not change.
- Writes are confined to `thoughts/shared/research/`, and only when a document
  is warranted (see Complexity Gating).
- Read-only git: `log`, `blame`, `diff`, `show` only — never commit, branch,
  checkout, push, or stash.
- No state-changing commands: no package installs, migrations, or builds.
- If the user asks you to implement, decline within this command and point to
  `/vad4nus:create-plan` → `/vad4nus:implement-plan`.

## Complexity Gating

Scale the process to the question — do not run the full pipeline by default.
Classify first, then say your classification and approach to the user in one
sentence (e.g. "This is a focused question about X — I'll check Y directly.").

| Tier    | Signals | Process |
| ------- | ------- | ------- |
| Simple  | One factual question about one component ("where/what/how does X") | Read the relevant files yourself; at most ONE vad4nus:codebase-locator agent. No TodoWrite, no research document. Answer in chat. |
| Medium  | 2–3 related questions, or one question spanning components | 1–3 targeted agents, synthesis in chat. Write a research document only if the user asks or the findings must be preserved. |
| Complex | Broad or architectural investigation, a task spec to decompose, or an explicit request for a research document | Full pipeline below (steps 1–9): decompose, TodoWrite, parallel agents, research document. |

When in doubt between two tiers, pick the lighter one and escalate mid-flight if
findings demand it — and tell the user you are escalating and why. Before
spawning any agents, state in 1–2 sentences what is being investigated and why.

## Final Response (mandatory)

The very last thing in your turn — after every tool call, agent result, and
file write — MUST be a chat message to the user (in their language) containing:

1. **Answer / outcome** — what was found, in 2–6 sentences.
2. **Key references** — the most important `file:line` pointers.
3. **Artifacts** — full path of the research document, or "no document written".
4. **Next steps** — how to verify, and an offer to answer follow-ups.

Never end the turn with a tool call. Writing the research document is NOT a
substitute for this message.

## Full pipeline (Complex tier; Medium when a document is warranted):

For the Simple tier, skip directly to the Final Response after reading the relevant files.

1. **Read any directly mentioned files first:**
   - If the user mentions specific files (tickets, docs, JSON), read them FULLY first
   - **IMPORTANT**: Use the Read tool WITHOUT limit/offset parameters to read entire files
   - **CRITICAL**: Read these files yourself in the main context before spawning any sub-tasks
   - This ensures you have full context before decomposing the research

2. **Analyze and decompose the research question:**
   - Break down the user's query into composable research areas
   - Take time to ultrathink about the underlying patterns, connections, and architectural implications the user might be seeking
   - Identify specific components, patterns, or concepts to investigate
   - Create a research plan using TodoWrite to track all subtasks
   - Consider which directories, files, or architectural patterns are relevant

3. **Spawn parallel sub-agent tasks for comprehensive research:**
   - Create multiple Task agents to research different aspects concurrently

   The key is to use these agents intelligently:
   - Start with locator agents to find what exists
   - Then use analyzer agents on the most promising findings
   - Run multiple agents in parallel when they're searching for different things
   - Each agent knows its job - just tell it what you're looking for
   - Don't write detailed prompts about HOW to search - the agents already know

4. **Wait for all sub-agents to complete and synthesize findings:**
   - IMPORTANT: Wait for ALL sub-agent tasks to complete before proceeding
   - Compile all sub-agent results (both codebase and thoughts findings)
   - Prioritize live codebase findings as primary source of truth
   - Use thoughts/ findings as supplementary historical context
   - Connect findings across different components
   - Include specific file paths and line numbers for reference
   - Verify all thoughts/ paths are correct (e.g., thoughts/allison/ not thoughts/shared/ for personal files)
   - Highlight patterns, connections, and architectural decisions
   - Answer the user's specific questions with concrete evidence
   - **No-results fallback**: if the agents surface no similar features or relevant code, do NOT return an empty finding. Document the project foundations instead, under a `## Note: No Similar Features Found` heading — stack & versions (from manifest files), how a new module/feature is conventionally started, the architecture pattern (MVC / service layer / hexagonal / monorepo), naming conventions, where tests live, and an entry-point map (top-level routes/handlers/CLI commands) as navigation anchors.
   - **Command resolution ladder** (first match wins) whenever you report a test or lint command — never invent one:
     - Test: `package.json` `scripts.test` → manifest detection (`Cargo.toml`→`cargo test`, `go.mod`→`go test ./...`, `Gemfile`→`bundle exec rspec`, `pyproject.toml`/`setup.py`→`pytest`, `mix.exs`→`mix test`) → `Makefile` `test` target → "test command unknown — check project docs".
     - Lint: `package.json` `scripts.lint` → manifest detection (`cargo clippy`, `go vet ./...`, `bundle exec rubocop`, `ruff check .`/`flake8`) → `Makefile` `lint` target → "lint command unknown — check project docs".

5. **Gather metadata for the research document:**
   - generate all relevant metadata
   - Filename: `thoughts/shared/research/YYYY-MM-DD-ENG-XXXX-description.md`
     - Format: `YYYY-MM-DD-ENG-XXXX-description.md` where:
       - YYYY-MM-DD is today's date
       - ENG-XXXX is the ticket number (omit if no ticket)
       - description is a brief kebab-case description of the research topic
     - Examples:
       - With ticket: `2025-01-08-ENG-1478-parent-child-tracking.md`
       - Without ticket: `2025-01-08-authentication-flow.md`

6. **Generate research document:**
   - Use the metadata gathered in step 4
   - Structure the document with YAML frontmatter followed by content:

     ```markdown
     ---
     date: [Current date and time with timezone in ISO format]
     researcher: [Researcher name]
     git_commit: [Current commit hash]
     branch: [Current branch name]
     repository: [Repository name]
     topic: "[User's Question/Topic]"
     tags: [research, codebase, relevant-component-names]
     status: complete
     last_updated: [Current date in YYYY-MM-DD format]
     last_updated_by: [Researcher name]
     ---

     # Research: [User's Question/Topic]

     **Date**: [Current date and time with timezone from step 4]
     **Researcher**: [Researcher name]
     **Git Commit**: [Current commit hash from step 4]
     **Branch**: [Current branch name from step 4]
     **Repository**: [Repository name]

     ## Research Question

     [Original user query]

     ## Summary

     [High-level findings answering the user's question]

     ## Detailed Findings

     ### [Component/Area 1]

     - Finding with reference ([file.ext:line](link))
     - Connection to other components
     - Implementation details

     ### [Component/Area 2]

     ...

     ## Code References

     - `path/to/file.py:123` - Description of what's there
     - `another/file.ts:45-67` - Description of the code block

     ## Architecture Insights

     [Patterns, conventions, and design decisions discovered]

     ## Historical Context (from thoughts/)

     [Relevant insights from thoughts/ directory with references]

     - `thoughts/shared/something.md` - Historical decision about X
     - `thoughts/local/notes.md` - Past exploration of Y
       Note: Paths exclude "searchable/" even if found there

     ## Related Research

     [Links to other research documents in thoughts/shared/research/]

     ## Open Questions

     [Any areas that need further investigation]
     ```

7. **Add GitHub permalinks (if applicable):**
   - Check if on main branch or if commit is pushed: `git branch --show-current` and `git status`
   - If on main/master or pushed, generate GitHub permalinks:
     - Get repo info: `gh repo view --json owner,name`
     - Create permalinks: `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`
   - Replace local file references with permalinks in the document

8. **Sync and present findings:**
   - Deliver the Final Response (see "Final Response (mandatory)" above) as the last message of the turn, in the user's language, including the research document path and key file references.

9. **Handle follow-up questions:**
   - If the user has follow-up questions, append to the same research document
   - Update the frontmatter fields `last_updated` and `last_updated_by` to reflect the update
   - Add `last_updated_note: "Added follow-up research for [brief description]"` to frontmatter
   - Add a new section: `## Follow-up Research [timestamp]`
   - Spawn new sub-agents as needed for additional investigation
   - Continue updating the document and syncing

## Important notes:

- For Complex-tier research, use parallel Task agents to maximize efficiency and minimize context usage; for Simple questions, do not spawn agents you don't need
- Always run fresh codebase research - never rely solely on existing research documents
- The thoughts/ directory provides historical context to supplement live findings
- Focus on finding concrete file paths and line numbers for developer reference
- Research documents should be self-contained with all necessary context
- Each sub-agent prompt should be specific and focused on read-only operations
- Consider cross-component connections and architectural patterns
- Include temporal context (when the research was conducted)
- Link to GitHub when possible for permanent references
- Keep the main agent focused on synthesis, not deep file reading
- Encourage sub-agents to find examples and usage patterns, not just definitions
- Explore all of thoughts/ directory, not just research subdirectory
- **File reading**: Always read mentioned files FULLY (no limit/offset) before spawning sub-tasks
- **Critical ordering**: Follow the numbered steps exactly
  - ALWAYS read mentioned files first before spawning sub-tasks (step 1)
  - ALWAYS wait for all sub-agents to complete before synthesizing (step 4)
  - ALWAYS gather metadata before writing the document (step 5 before step 6)
  - NEVER write the research document with placeholder values
- **Path handling**: The thoughts/searchable/ directory contains hard links for searching
  - Always document paths by removing ONLY "searchable/" - preserve all other subdirectories
  - Examples of correct transformations:
    - `thoughts/searchable/allison/old_stuff/notes.md` → `thoughts/allison/old_stuff/notes.md`
    - `thoughts/searchable/shared/prs/123.md` → `thoughts/shared/prs/123.md`
    - `thoughts/searchable/global/shared/templates.md` → `thoughts/global/shared/templates.md`
  - NEVER change allison/ to shared/ or vice versa - preserve the exact directory structure
  - This ensures paths are correct for editing and navigation
- **Frontmatter consistency**:
  - Always include frontmatter at the beginning of research documents
  - Keep frontmatter fields consistent across all research documents
  - Update frontmatter when adding follow-up research
  - Use snake_case for multi-word field names (e.g., `last_updated`, `git_commit`)
  - Tags should be relevant to the research topic and components studied
