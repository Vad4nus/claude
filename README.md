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
