#!/usr/bin/env bash
# Install repo git hooks (commit-msg, pre-commit, pre-push)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x .githooks/commit-msg .githooks/pre-commit .githooks/pre-push
chmod +x scripts/lib/check-no-ai-attribution.sh scripts/validate-commit-msg.sh

if git rev-parse --git-dir >/dev/null 2>&1; then
  git config core.hooksPath .githooks
  echo "✅ Git hooks installed (core.hooksPath=.githooks)"
else
  echo "⚠️  Not a git repo yet. Run 'git init' first, then re-run this script."
fi

cat <<'EOF'
   Hooks enabled:
   • commit-msg  — Conventional Commits + block Cursor/Claude/AI attribution
   • pre-commit  — block .cursor/ .claude/ and other agent config paths
   • pre-push    — block branch names containing AI tool references
EOF
