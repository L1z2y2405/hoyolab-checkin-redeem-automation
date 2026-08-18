#!/usr/bin/env bash
# Reject commit messages, branch names, or text containing AI / agent attribution.
# Used by git hooks and CI.

set -euo pipefail

# Case-insensitive extended regex — keep in sync with docs/GITLAB_SETUP.md
BANNED_REGEX='(co-authored-by:[[:space:]]*.*(<[^>]*>)?(cursor|claude|anthropic|openai|chatgpt|copilot|github-copilot|windsurf|cody|tabnine|devin|gemini|ai[[:space:]-]?agent|auto[[:space:]-]?agent|noreply@anthropic\.com)|\b(cursor[[:space:]]+(ide|agent|ai|bot|editor)|cursor\.com|cursor\.sh)\b|\b(claude[[:space:]]*(code|sonnet|opus|haiku|ai|bot)|anthropic)\b|\b(chatgpt|openai|github[[:space:]]*copilot|copilot[[:space:]]*ai)\b|\b(windsurf|cody|tabnine|devin[[:space:]]*ai|gemini[[:space:]]*code)\b|\bai[[:space:]-]?generated\b|\bgenerated[[:space:]]+by[[:space:]]+(cursor|claude|ai|copilot|chatgpt)\b|\bassisted[[:space:]]+by[[:space:]]+(cursor|claude|ai|copilot|chatgpt)\b|\bwritten[[:space:]]+by[[:space:]]+(cursor|claude|ai)\b)'

check_no_ai_attribution() {
  local TEXT="${1:-}"
  local CONTEXT="${2:-commit message}"

  if [[ -z "${TEXT// }" ]]; then
    return 0
  fi

  local LOWER
  LOWER="$(printf '%s' "$TEXT" | tr '[:upper:]' '[:lower:]')"

  if printf '%s\n' "$LOWER" | grep -Eiq "$BANNED_REGEX"; then
    cat >&2 <<EOF
❌ Blocked: ${CONTEXT} must not reference AI coding tools or agents.

Remove all mentions of Cursor, Claude, Anthropic, Copilot, ChatGPT, and similar.
Remove Co-Authored-By / Signed-off-by lines that credit AI tools.

Human authors only — no AI attribution in commits, branches, or MR titles.

See CONTRIBUTING.md → "No AI attribution".
EOF
    return 1
  fi

  return 0
}
