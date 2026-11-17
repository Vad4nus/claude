---
description: "List my open-sprint Jira Server issues, or download one issue with all attachments for planning. No args: list the issues. ISSUE-KEY: download it to ~/Jira/<host>/<KEY>/. E.g. /vad4nus:fetch-server-jira-tasks W30-891"
argument-hint: "[ISSUE-KEY]"
model: haiku
effort: low
disable-model-invocation: true
---

# fetch-server-jira-tasks

Connects to the Jira Server MCP to list or download issues. No arguments = list. One argument = download.

## Without an argument

Call `mcp__plugin_vad4nus_jira-server__my_sprint_issues` with no parameters.

Print the returned table as-is.

End with:

```
To download a full issue: /vad4nus:fetch-server-jira-tasks <KEY>
```

## With one argument

The argument is the issue key (e.g. `WL-123`).

Call `mcp__plugin_vad4nus_jira-server__fetch_issue` with `key` set to the argument.

Print the folder path, attachment count and size returned by the tool.

End with the command the tool suggests, which is:

```
/vad4nus:create-plan <folder>/ticket.md
```

## Errors

Print the error message from the server unchanged. Do not retry.

Never ask for the PAT in chat and never run the Keychain command yourself. A missing PAT error names a `security add-generic-password` command: tell the user to run it in their own terminal, then call the tool again: the server reads the Keychain on every call, no reconnect needed.

## Never

- Read attachment files into context unless the user explicitly asks.
- Call any Jira tool other than the two listed above.
