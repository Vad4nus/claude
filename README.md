# vad4nus

Personal Claude Code plugin. Skills run as `/vad4nus:<skill>`.

## Upstreams

| Path | Forked from | At |
| ---- | ----------- | -- |
| `skills/cross-model-deliberation/` | `https://github.com/Marcussy34/claude-codex-council` | `f28ec13` |
| `skills/thermo-nuclear-code-quality-review/` (verbatim, MIT), `agents/thermo-nuclear-code-quality-review.md` (adapted) | `https://github.com/cursor/plugins` `cursor-team-kit/` | `ccb5507` |

## Install

```bash
claude plugin marketplace add ~/StudioProjects/vad4nus-claude
claude plugin install vad4nus@vad4nus
```

Claude Code loads a cached copy, not this directory. `plugin.json` has no `version`, so the version is the commit SHA. To pick up edits:

```bash
git commit -am "..."
claude plugin update vad4nus@vad4nus
```

Then `/reload-plugins` in the session.

## New Mac setup

Check what is there; the script installs nothing and prints the command for each gap:

```bash
bash ~/StudioProjects/vad4nus-claude/scripts/doctor.sh
```

What the skills use, as set up on the first Mac (Intel, 2026-11):

| Tool | Version there | Install | Used by |
| --- | --- | --- | --- |
| uv | 0.12 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (must land in `~/.local/bin`, `plugin.json` runs `${HOME}/.local/bin/uv`) | Jira MCP server |
| python3 | 3.15 | `brew install python` | ios-run, ios-qa |
| codebase-memory-mcp | 0.9.0 | `curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh \| bash`, then restart Claude | create-plan, implement-plan |
| node + Codex CLI | 24 / 0.160 | `brew install node && npm install -g @openai/codex && codex login` | create-plan Codex review, cross-model-deliberation |
| Codex plugin | 1.0.6 | `claude plugin marketplace add openai/codex-plugin-cc && claude plugin install codex@openai-codex`, then `/codex:setup` | same |
| Xcode | 26.3 | App Store; `xcodebuild -downloadPlatform iOS` for a simulator runtime | ios-run, ios-qa, ios-testflight, kmp-verify |
| xcodegen | 2.44 | `brew install xcodegen` | ios-run, kmp-verify, orchestrate |
| swiftlint | 0.63 | `brew install swiftlint` | kmp-verify |
| AXe | 2.0.4 | `brew install cameroncooke/axe/axe` | ios-qa |
| JDK 17 | 17.0.16 | `brew install openjdk@17` | kmp-verify (Gradle) |
| gh | 2.102 | `brew install gh && gh auth login` | research-codebase (optional) |

By hand, no script can do these:

- Codex `max` effort for cross-model-deliberation: add `"max"` to `VALID_REASONING_EFFORTS` in `~/.claude/plugins/cache/openai-codex/codex/<version>/scripts/codex-companion.mjs`. Every Codex plugin update undoes it. `~/.codex/config.toml` there: `model = "gpt-6-astra"`.
- Jira PAT in the Keychain (see Jira Server below).
- TestFlight / App Store: the Apple ID with App Store Connect access signed in at Xcode → Settings → Accounts.
- `~/.claude/settings.json` there has `"env": { "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS": "3" }`: a cap on parallel agents, a budget, not a target.
- The plugin itself: clone this repo to `~/StudioProjects/vad4nus-claude` (the marketplace is a `directory` source), then Install above.

## Jira Server

Fetches issues from a self-hosted Jira Server instance.

### Config

Non-secret fields: terminal `claude` → `/plugin` → Installed → vad4nus → Configure options (read-only in the desktop app).

| Field | Default | Notes |
| --- | --- | --- |
| `jira_server_url` | `https://jira.jetru.by` | Base URL of your Jira Server |
| `jira_server_project` | — | Project key or comma-separated list; empty = all |
| `jira_download_dir` | `~/Jira` | Root dir for downloaded issues |

PAT: create one in Jira (profile → Personal Access Tokens → Create token), then store it from your own terminal. The prompt hides the input; change or delete it later in Keychain Access under `vad4nus-jira-server`:

```bash
security add-generic-password -U -s vad4nus-jira-server -a jira -w
```

Why not the plugin dialog: Claude Code 2.1.293–2.1.294 does not substitute values saved in user `pluginConfigs` (or the sensitive `jira_server_token`) into the MCP server env; only defaults and `--settings` values arrive. The server therefore reads `pluginConfigs` from `~/.claude/settings.json` itself and the PAT from the Keychain item above, on every tool call, so a replaced PAT works without a restart. The PAT field was removed from the plugin config (2026-10-20): Claude Code did pass a PAT saved in that form through env, a stale one, and it overrode the valid Keychain PAT with constant 401s. `JIRA_TOKEN` in env is only a fallback when the Keychain item is missing.

After changing any value or running `claude plugin update`, restart the server: a new session or restarting the desktop app. `/reload-plugins` does not restart the MCP server, even when the plugin version changed.

### Commands

```
/vad4nus:fetch-server-jira-tasks
```

Lists your open-sprint issues (not Done) as a Markdown table.

```
/vad4nus:fetch-server-jira-tasks WL-123
```

Downloads the full issue to `~/Jira/<host>/WL-123/`:
- `ticket.md` — fields, description, comments, subtasks, links, attachment list
- `attachments/` — every attachment

Then suggests `/vad4nus:create-plan ~/Jira/<host>/WL-123/ticket.md`.
