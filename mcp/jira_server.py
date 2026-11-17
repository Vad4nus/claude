#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mcp>=1.2,<2",
#   "httpx>=0.27,<1",
# ]
# ///

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("jira-server")

KEYCHAIN_SERVICE = "vad4nus-jira-server"
PLUGIN_ID = "vad4nus@vad4nus"


def setting(name: str) -> str:
    val = os.environ.get(name, "")
    if val.startswith("${"):
        return ""
    return val


def saved_options(settings_path: Path) -> dict:
    try:
        settings = json.loads(settings_path.read_text())
    except (OSError, ValueError):
        return {}
    return settings.get("pluginConfigs", {}).get(PLUGIN_ID, {}).get("options", {})


def keychain_token() -> str:
    try:
        out = subprocess.run(
            ["/usr/bin/security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


OPTIONS = saved_options(Path(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude")).expanduser() / "settings.json")


def option(key: str, env_name: str) -> str:
    return str(OPTIONS.get(key) or "") or setting(env_name)


JIRA_URL = option("jira_server_url", "JIRA_URL").rstrip("/")
JIRA_PROJECT = option("jira_server_project", "JIRA_PROJECT")
JIRA_DOWNLOAD_DIR = os.path.expanduser(option("jira_download_dir", "JIRA_DOWNLOAD_DIR") or "~/Jira")
NO_TOKEN = (
    f"Error: no Jira PAT. Store it in the macOS Keychain from your own terminal (hidden prompt): "
    f"security add-generic-password -U -s {KEYCHAIN_SERVICE} -a jira -w"
)
BAD_TOKEN = (
    f"Jira rejected the PAT (401). Replace it from your own terminal (hidden prompt): "
    f"security add-generic-password -U -s {KEYCHAIN_SERVICE} -a jira -w"
)
SPRINT_SCHEMA_SUFFIX = ":gh-sprint"


def build_jql(projects: str) -> str:
    base = "assignee = currentUser() AND sprint in openSprints() AND statusCategory != Done ORDER BY priority DESC"
    keys = [k.strip().upper() for k in projects.split(",") if k.strip()]
    if keys:
        project_list = ", ".join(keys)
        return f"project in ({project_list}) AND {base}"
    return base


def safe_filename(name: str) -> str:
    name = os.path.basename(name)
    name = name.replace("/", "_").replace("\\", "_").replace("\x00", "_")
    name = name.lstrip(".")
    return name or "attachment"


def unique_name(name: str, taken: set, attachment_id: str) -> str:
    if name not in taken:
        return name
    path = Path(name)
    stem = path.stem
    suffix = path.suffix
    return f"{stem}-{attachment_id}{suffix}"


def issue_dir(download_dir: str, base_url: str, key: str) -> Path:
    host = urlparse(base_url).hostname or base_url
    base = Path(download_dir).resolve()
    host_dir = (base / host).resolve()
    target = (host_dir / key).resolve()
    if not str(target).startswith(str(host_dir) + os.sep) and str(target) != str(host_dir):
        raise ValueError(f"Resolved path {target} escapes host directory {host_dir}")
    return target


def is_login_page(response_content_type: str, expected_mime: str, final_url: str) -> bool:
    ct = response_content_type.split(";")[0].strip().lower()
    expected_is_html = "html" in expected_mime.lower()
    if ct == "text/html" and not expected_is_html:
        return True
    if "login" in final_url.lower():
        return True
    return False


def sprint_entry(s) -> tuple[str, str]:
    if isinstance(s, dict):
        return str(s.get("state", "")), str(s.get("name", ""))
    state = re.search(r"[\[,]state=(\w+)", str(s))
    name = re.search(r"[\[,]name=(.*?)(?:,\w+=|\]$)", str(s))
    return (state[1] if state else ""), (name[1] if name else "")


def open_sprint_names(issue: dict) -> list:
    fields = issue.get("fields", {})
    names = []
    for fid, schema in (issue.get("schema") or {}).items():
        if not str((schema or {}).get("custom", "")).endswith(SPRINT_SCHEMA_SUFFIX):
            continue
        for s in fields.get(fid) or []:
            state, name = sprint_entry(s)
            if name and state.lower() != "closed":
                names.append(name)
    return names


def render_ticket_md(issue: dict, comments: list, saved: list) -> str:
    fields = issue.get("fields", {})
    key = issue.get("key", "")

    def fname(obj, fallback=""):
        if obj is None:
            return fallback
        return obj.get("displayName") or obj.get("name") or fallback

    def fstr(obj, fallback=""):
        if obj is None:
            return fallback
        if isinstance(obj, str):
            return obj
        return obj.get("name") or fallback

    sprint = ", ".join(open_sprint_names(issue))

    parent = fields.get("parent")
    parent_str = f"{parent['key']}: {parent['fields']['summary']}" if parent else ""

    labels = ", ".join(fields.get("labels") or [])
    components = ", ".join(c.get("name", "") for c in (fields.get("components") or []))
    fix_versions = ", ".join(v.get("name", "") for v in (fields.get("fixVersions") or []))

    lines = [
        "| Field | Value |",
        "| --- | --- |",
        f"| Key | {key} |",
        f"| Summary | {fields.get('summary', '')} |",
        f"| Type | {fstr(fields.get('issuetype'))} |",
        f"| Status | {fstr(fields.get('status'))} |",
        f"| Priority | {fstr(fields.get('priority'))} |",
        f"| Assignee | {fname(fields.get('assignee'))} |",
        f"| Reporter | {fname(fields.get('reporter'))} |",
        f"| Sprint | {sprint} |",
        f"| Parent | {parent_str} |",
        f"| Labels | {labels} |",
        f"| Components | {components} |",
        f"| Fix Versions | {fix_versions} |",
        f"| Created | {fields.get('created', '')} |",
        f"| Updated | {fields.get('updated', '')} |",
        "",
        "## Description",
        "",
        fields.get("description") or "_no description_",
        "",
    ]

    if comments:
        lines += ["## Comments", ""]
        for c in comments:
            author = fname(c.get("author"))
            date = c.get("created", "")
            body = c.get("body", "")
            lines += [f"**{author}** ({date})", "", body, ""]

    subtasks = fields.get("subtasks") or []
    if subtasks:
        lines += ["## Subtasks", ""]
        for s in subtasks:
            lines.append(f"- {s['key']}: {s['fields']['summary']}")
        lines.append("")

    links = fields.get("issuelinks") or []
    if links:
        lines += ["## Links", ""]
        for lk in links:
            ltype = lk.get("type", {}).get("name", "")
            if "outwardIssue" in lk:
                rel = lk["type"].get("outward", ltype)
                other = lk["outwardIssue"]
            elif "inwardIssue" in lk:
                rel = lk["type"].get("inward", ltype)
                other = lk["inwardIssue"]
            else:
                continue
            lines.append(f"- {rel}: {other['key']} {other['fields']['summary']}")
        lines.append("")

    if saved:
        lines += ["## Attachments", "", "| Filename | Size |", "| --- | --- |"]
        for fname_val, size in saved:
            lines.append(f"| {fname_val} | {size} bytes |")
        lines.append("")

    return "\n".join(lines)


def jira_token() -> str:
    return keychain_token() or setting("JIRA_TOKEN")


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


@mcp.tool(annotations={"readOnlyHint": True})
def my_sprint_issues() -> str:
    """List issues assigned to you in the open sprint that are not yet Done."""
    if not JIRA_URL:
        return "Error: jira_server_url is not configured in the vad4nus plugin settings."
    token = jira_token()
    if not token:
        return NO_TOKEN

    jql = build_jql(JIRA_PROJECT)
    fields = "summary,status,issuetype,priority"
    rows = []
    start = 0
    total = None

    with httpx.Client(headers=_headers(token), follow_redirects=True, timeout=30) as client:
        while True:
            resp = client.post(
                f"{JIRA_URL}/rest/api/2/search",
                json={"jql": jql, "startAt": start, "maxResults": 100, "fields": fields.split(",")},
            )
            if resp.status_code == 401:
                return BAD_TOKEN
            resp.raise_for_status()
            data = resp.json()
            if total is None:
                total = data["total"]
            for issue in data["issues"]:
                f = issue["fields"]
                rows.append({
                    "key": issue["key"],
                    "type": (f.get("issuetype") or {}).get("name", ""),
                    "status": (f.get("status") or {}).get("name", ""),
                    "priority": (f.get("priority") or {}).get("name", ""),
                    "summary": f.get("summary", ""),
                })
            start += len(data["issues"])
            if start >= total:
                break

    if not rows:
        return "No open-sprint issues assigned to you."

    header = "| Key | Type | Status | Priority | Summary |"
    sep = "| --- | --- | --- | --- | --- |"
    table = [header, sep]
    for r in rows:
        table.append(f"| {r['key']} | {r['type']} | {r['status']} | {r['priority']} | {r['summary']} |")
    return "\n".join(table)


@mcp.tool(annotations={"readOnlyHint": True})
def fetch_issue(key: str) -> str:
    """Download a Jira issue with all its attachments to ~/Jira/<host>/<KEY>/."""
    if not JIRA_URL:
        return "Error: jira_server_url is not configured in the vad4nus plugin settings."
    token = jira_token()
    if not token:
        return NO_TOKEN

    if not re.match(r"^[A-Za-z][A-Za-z0-9_]*-[0-9]+$", key):
        return f"Error: '{key}' is not a valid Jira issue key."
    key = key.upper()

    try:
        target = issue_dir(JIRA_DOWNLOAD_DIR, JIRA_URL, key)
    except ValueError as e:
        return f"Error: {e}"

    partial = target.parent / f"{key}.partial"

    with httpx.Client(headers=_headers(token), follow_redirects=True, timeout=60) as client:
        resp = client.get(f"{JIRA_URL}/rest/api/2/issue/{key}?fields=*all&expand=schema")
        if resp.status_code == 401:
            return BAD_TOKEN
        if resp.status_code == 404:
            return f"Error: Issue {key} not found."
        resp.raise_for_status()
        issue = resp.json()

        fields = issue.get("fields", {})
        comment_data = fields.get("comment", {})
        comments = comment_data.get("comments", [])
        comment_total = comment_data.get("total", 0)

        if comment_total > len(comments):
            start = len(comments)
            while start < comment_total:
                cr = client.get(
                    f"{JIRA_URL}/rest/api/2/issue/{key}/comment",
                    params={"startAt": start, "maxResults": 100},
                )
                cr.raise_for_status()
                cd = cr.json()
                page = cd.get("comments", [])
                comments.extend(page)
                start += len(page)
                if not page:
                    break

        attachments = fields.get("attachment") or []

        if partial.exists():
            import shutil
            shutil.rmtree(partial)
        partial_att = partial / "attachments"
        partial_att.mkdir(parents=True)

        saved = []
        taken: set = set()
        total_size = 0

        try:
            for att in attachments:
                raw_name = att.get("filename", "")
                att_id = str(att.get("id", ""))
                mime = att.get("mimeType", "application/octet-stream")
                content_url = att.get("content", "")

                name = safe_filename(raw_name)
                name = unique_name(name, taken, att_id)
                taken.add(name)

                att_resp = client.get(content_url)
                if att_resp.status_code != 200:
                    raise RuntimeError(
                        f"Attachment '{name}' returned HTTP {att_resp.status_code}. Aborting."
                    )
                ct = att_resp.headers.get("content-type", "")
                final_url = str(att_resp.url)
                if is_login_page(ct, mime, final_url):
                    raise RuntimeError(
                        f"Attachment '{name}' redirected to a login page (PAT may not be accepted for attachments on this Jira version). Aborting."
                    )

                dest = partial_att / name
                dest.write_bytes(att_resp.content)
                size = len(att_resp.content)
                total_size += size
                saved.append((name, size))

        except Exception as e:
            import shutil
            if partial.exists():
                shutil.rmtree(partial)
            return f"Error: {e}"

        md = render_ticket_md(issue, comments, saved)
        (partial / "ticket.md").write_text(md, encoding="utf-8")

        import shutil
        if target.exists():
            shutil.rmtree(target)
        partial.rename(target)

    att_count = len(saved)
    size_kb = total_size // 1024
    ticket_path = target / "ticket.md"
    return (
        f"Downloaded {key} to {target}\n"
        f"  {att_count} attachment(s), {size_kb} KB total\n"
        f"  ticket: {ticket_path}\n"
        f"\n"
        f"Next: /vad4nus:create-plan {ticket_path}"
    )


def _self_test():
    assert build_jql("") == "assignee = currentUser() AND sprint in openSprints() AND statusCategory != Done ORDER BY priority DESC"
    assert build_jql(" wl , ios ") == "project in (WL, IOS) AND assignee = currentUser() AND sprint in openSprints() AND statusCategory != Done ORDER BY priority DESC"

    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("..") == "attachment"
    assert safe_filename(".hidden") == "hidden"
    assert safe_filename("a\\b.png") == "a_b.png"
    assert safe_filename("") == "attachment"

    taken: set = {"file.png"}
    assert unique_name("file.png", taken, "42") == "file-42.png"
    assert unique_name("other.png", taken, "42") == "other.png"

    test_jira = "https://jira.example.test"
    d = issue_dir("/tmp/Jira", test_jira, "WL-1")
    assert str(d).endswith("WL-1")
    assert "jira.example.test" in str(d)

    try:
        issue_dir("/tmp/Jira", test_jira, "../x")
        assert False, "should raise"
    except ValueError:
        pass

    assert is_login_page("text/html; charset=utf-8", "image/png", f"{test_jira}/attachment/123") is True
    assert is_login_page("image/png", "image/png", f"{test_jira}/attachment/123") is False
    assert is_login_page("text/html", "text/html", f"{test_jira}/attachment/123") is False
    assert is_login_page("application/json", "application/json", f"{test_jira}/login?next=/foo") is True

    server_sprint = "com.atlassian.greenhopper.service.sprint.Sprint@1f2e[id=7,rapidViewId=3,state=ACTIVE,name=W30, Sprint 12,startDate=2026-10-01T10:00:00.000Z,goal=]"
    closed_sprint = "com.atlassian.greenhopper.service.sprint.Sprint@9a[id=6,rapidViewId=3,state=CLOSED,name=W30 Sprint 11,goal=]"
    assert sprint_entry(server_sprint) == ("ACTIVE", "W30, Sprint 12")
    assert sprint_entry({"state": "future", "name": "Next"}) == ("future", "Next")
    assert sprint_entry("garbage") == ("", "")
    sprint_issue = {
        "schema": {"customfield_10104": {"custom": "com.pyxis.greenhopper.jira:gh-sprint"}, "summary": {"system": "summary"}},
        "fields": {"customfield_10104": [closed_sprint, server_sprint, {"state": "future", "name": "Next"}]},
    }
    assert open_sprint_names(sprint_issue) == ["W30, Sprint 12", "Next"]
    assert open_sprint_names({"fields": {}}) == []

    os.environ["TEST_UNSET"] = "${user_config.jira_server_project}"
    assert setting("TEST_UNSET") == ""
    del os.environ["TEST_UNSET"]

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "settings.json"
        p.write_text(json.dumps({"pluginConfigs": {PLUGIN_ID: {"options": {"jira_server_project": "W30"}}}}))
        assert saved_options(p) == {"jira_server_project": "W30"}
        p.write_text("{not json")
        assert saved_options(p) == {}
        assert saved_options(Path(tmp) / "missing.json") == {}

    print("OK")
    sys.exit(0)


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        _self_test()
    mcp.run(transport="stdio")
