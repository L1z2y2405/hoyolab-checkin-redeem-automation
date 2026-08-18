#!/usr/bin/env bash
# Validate commit message + scan MR/push commits in CI for AI attribution.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/check-no-ai-attribution.sh
source "$ROOT/scripts/lib/check-no-ai-attribution.sh"

if [[ "${1:-}" == "--range" ]]; then
  BASE="${2:?base ref required}"
  HEAD="${3:-HEAD}"
  echo "🔍 Checking commits ${BASE}..${HEAD} for AI attribution..."
  while IFS= read -r sha; do
    [[ -z "$sha" ]] && continue
    msg="$(git log -1 --format=%B "$sha")"
    subject="$(git log -1 --format=%s "$sha")"
    check_no_ai_attribution "$msg" "commit ${sha:0:8} ($subject)"
  done < <(git rev-list --reverse "${BASE}..${HEAD}")
  echo "✅ No AI attribution in commit range"
  exit 0
fi

MSG="${1:-$(git log -1 --pretty=%B)}"
check_no_ai_attribution "$MSG" "commit message"
.githooks/commit-msg <(printf '%s\n' "$MSG")
echo "✅ Commit message OK: $(echo "$MSG" | head -1)"
