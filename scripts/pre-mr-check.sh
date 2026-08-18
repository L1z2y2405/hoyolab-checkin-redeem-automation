#!/usr/bin/env bash
# Local gate before git push / opening a GitLab MR.
# Agents and humans must run this and get exit 0 first.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/lib/check-no-ai-attribution.sh
source "$ROOT/scripts/lib/check-no-ai-attribution.sh"

BASE="${1:-origin/main}"
if ! git rev-parse --verify "$BASE" >/dev/null 2>&1; then
  echo "Fetching $BASE ..."
  git fetch origin main --depth=50 >/dev/null 2>&1 || true
  BASE="origin/main"
fi

echo "== Branch name =="
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
check_no_ai_attribution "$BRANCH" "branch name '$BRANCH'"
echo "OK: $BRANCH"

echo "== Commit messages ($BASE..HEAD) =="
"$ROOT/scripts/validate-commit-msg.sh" --range "$BASE" HEAD

echo "== Tip commit trailers (must be empty of AI co-authors) =="
MSG="$(git log -1 --format='%B')"
check_no_ai_attribution "$MSG" "tip commit message"
TRAILERS="$(git log -1 --format='%(trailers)')"
if printf '%s\n' "$TRAILERS" | grep -Eiq 'co-authored-by:'; then
  echo "❌ Tip commit still has Co-authored-by trailers:"
  printf '%s\n' "$TRAILERS"
  echo "See docs/PRE_MR_CHECKLIST.md → rewrite with git commit-tree"
  exit 1
fi
echo "OK: no AI trailers"

echo "== Ruff (tests) =="
if command -v ruff >/dev/null 2>&1; then
  RUFF=(ruff)
elif [[ -x "$ROOT/../.test-venv312/bin/ruff" ]]; then
  RUFF=("$ROOT/../.test-venv312/bin/ruff")
else
  python3 -m pip install --quiet 'ruff==0.8.4'
  RUFF=(python3 -m ruff)
fi
"${RUFF[@]}" check tests
"${RUFF[@]}" format --check tests
echo "OK: ruff"

echo
echo "✅ Pre-MR checks passed. Safe to push / open MR."
echo "   Checklist: docs/PRE_MR_CHECKLIST.md"
