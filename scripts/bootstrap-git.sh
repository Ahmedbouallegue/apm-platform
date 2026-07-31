#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .git ]; then
  git init
  git branch -M main
fi

git add -A
git status

if [ -n "$(git status --porcelain)" ]; then
  git commit -m "chore: bootstrap Sprint 0 — APM platform foundation"
fi

echo
echo "Next:"
echo "  gh repo create apm-platform --private --source=. --remote=origin --push"
