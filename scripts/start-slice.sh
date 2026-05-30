#!/usr/bin/env bash
# Usage: scripts/start-slice.sh NN   (e.g. scripts/start-slice.sh 05)
# Branches a new slice from a freshly pulled main and seeds its exchange file.
set -euo pipefail
N="${1:?usage: start-slice.sh NN (e.g. 05)}"
BRANCH="slice-${N}"
cd "$(git rev-parse --show-toplevel)"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Working tree not clean — commit or stash first." >&2; exit 1
fi
if git rev-parse --verify --quiet "$BRANCH" >/dev/null; then
  echo "Branch $BRANCH already exists." >&2; exit 1
fi

git checkout main
git pull origin main
git checkout -b "$BRANCH"

EX="docs/exchange/slice-${N}.md"
if [[ ! -f "$EX" ]]; then
  sed "s/Slice NN/Slice ${N}/" docs/exchange/_template.md > "$EX"
  git add "$EX"
  echo "Seeded $EX"
fi
echo "Ready on $BRANCH. Add docs/slices/slice-${N}.md, commit, then: git push -u origin $BRANCH"
