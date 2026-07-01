#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

read -r -p "Phase number, example 124: " PHASE_NUM
read -r -p "Commit description, example 'frame quality drill down': " DESC
read -r -p "Tag slug, example 'frame-quality-drill-down': " SLUG

if [ -z "$PHASE_NUM" ] || [ -z "$DESC" ] || [ -z "$SLUG" ]; then
  echo "ERROR: phase number, description, and slug are required."
  exit 1
fi

echo
echo "Starting full auto phase."
echo "This will run Cursor Agent, tests, commit, tag, and push."
echo

read -r -p "Type RUN FULL AUTO to continue: " CONFIRM

if [ "$CONFIRM" != "RUN FULL AUTO" ]; then
  echo "Canceled."
  exit 1
fi

if [ -n "$(git status --short)" ]; then
  echo "ERROR: repo is not clean before starting."
  git status --short
  exit 1
fi

CURSOR_AGENT_FORCE=1 ./scripts/run_next_phase_cursor.sh

echo
echo "Running backend/full project tests..."
make test

echo
echo "Running frontend tests/build..."
cd frontend
npm test
npm run build
cd ..

echo
echo "Cleaning runtime artifacts under data/dev..."
git restore data/dev/ 2>/dev/null || true

echo
echo "Final status before commit:"
git status --short
echo

git add .
git restore --staged data/dev/ 2>/dev/null || true

echo
echo "Staged files:"
git status --short
echo

read -r -p "Commit, tag, and push? Type yes: " PUSH_CONFIRM

if [ "$PUSH_CONFIRM" != "yes" ]; then
  echo "Canceled before commit."
  exit 1
fi

git commit -m "phase ${PHASE_NUM}: ${DESC}"
git tag "phase-${PHASE_NUM}-${SLUG}"
git push origin main --tags

echo
echo "Full auto phase complete."
