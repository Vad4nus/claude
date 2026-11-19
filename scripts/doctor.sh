#!/usr/bin/env bash
# Checks what the vad4nus skills need on this Mac and prints the install command for each gap.
# Installs nothing. Usage: bash scripts/doctor.sh
# Exit code: the number of missing required items.

missing=0
PATH="$HOME/.local/bin:$PATH"

ok()   { printf '  ok    %-22s %s\n' "$1" "$2"; }
gap()  { printf '  MISS  %-22s %s\n        → %s\n' "$1" "$2" "$3"; [ "$4" = optional ] || missing=$((missing + 1)); }

tool() { # name, install command, what needs it, [optional]
  local p v
  if p=$(command -v "$1"); then
    v=$("$p" --version 2>&1 | head -1)
    ok "$1" "$v"
  else
    gap "$1" "$3" "$2" "$4"
  fi
}

echo "Core"
tool git      "xcode-select --install"                                  "everything"
tool python3  "brew install python"                                     "ios-run (devicectl parsing), ios-qa"
tool uv       "curl -LsSf https://astral.sh/uv/install.sh | sh"         "Jira MCP server (plugin.json runs \${HOME}/.local/bin/uv)"
tool gh       "brew install gh && gh auth login"                        "research-codebase (GitHub permalinks)" optional

echo "Code index"
tool codebase-memory-mcp "curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash" \
                                                                        "create-plan, implement-plan (index_repository)"

echo "Codex (create-plan review, cross-model-deliberation)"
tool node     "brew install node"                                       "Codex CLI"
tool codex    "npm install -g @openai/codex && codex login"             "Codex review"
if grep -q '"codex@openai-codex": *true' "$HOME/.claude/settings.json" 2>/dev/null; then
  ok "codex plugin" "codex@openai-codex enabled"
else
  gap "codex plugin" "Claude Code plugin" "claude plugin marketplace add openai/codex-plugin-cc && claude plugin install codex@openai-codex, then /codex:setup"
fi
companion=$(ls -d "$HOME"/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs 2>/dev/null | tail -1)
if [ -n "$companion" ] && grep -q 'VALID_REASONING_EFFORTS = new Set(\[[^]]*"max"' "$companion"; then
  ok "codex effort max" "patched"
else
  gap "codex effort max" "cross-model-deliberation stops without it; plugin updates undo it" \
      "add \"max\" to VALID_REASONING_EFFORTS in ${companion:-<codex plugin>/scripts/codex-companion.mjs}" optional
fi

echo "iOS"
if v=$(xcodebuild -version 2>/dev/null | head -1); then ok "Xcode" "$v"; else gap "Xcode" "ios-run, ios-qa, ios-testflight, kmp-verify" "App Store → Xcode, then sudo xcode-select -s /Applications/Xcode.app"; fi
tool xcodegen  "brew install xcodegen"                                  "ios-run, kmp-verify, orchestrate"
tool swiftlint "brew install swiftlint"                                 "kmp-verify"
tool axe       "brew install cameroncooke/axe/axe"                      "ios-qa (accessibility tree instead of screenshots)"
if xcrun simctl list runtimes 2>/dev/null | grep -q '^iOS'; then
  ok "iOS runtime" "$(xcrun simctl list runtimes | grep '^iOS' | tail -1 | cut -d' ' -f1-2)"
else
  gap "iOS runtime" "ios-run, ios-qa" "xcodebuild -downloadPlatform iOS"
fi
echo "        TestFlight / App Store: sign the Apple ID with App Store Connect access into Xcode → Settings → Accounts."

echo "Android / KMP"
if v=$(java -version 2>&1 | head -1) && [[ "$v" == *'"17'* ]]; then ok "JDK 17" "$v"; else gap "JDK 17" "kmp-verify (Gradle 8.x)" "brew install openjdk@17"; fi

echo "Jira"
if security find-generic-password -s vad4nus-jira-server >/dev/null 2>&1; then
  ok "Jira PAT" "Keychain item vad4nus-jira-server"
else
  gap "Jira PAT" "fetch-server-jira-tasks" "security add-generic-password -U -s vad4nus-jira-server -a jira -w" optional
fi

echo
[ "$missing" -eq 0 ] && echo "All required items present." || echo "$missing required item(s) missing."
exit "$missing"
