#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "RadarArchive - Finish Phase"
echo

read -r -p "Phase number, example 124: " PHASE_NUM
read -r -p "Commit description, example 'frame quality drill down': " DESC
read -r -p "Tag slug, example 'frame-quality-drill-down': " SLUG

if [ -z "$PHASE_NUM" ] || [ -z "$DESC" ] || [ -z "$SLUG" ]; then
  echo "ERROR: phase number, description, and slug are required."
  exit 1
fi

echo
echo "Current git status:"
git status --short
echo

echo "This script will stage everything EXCEPT data/dev runtime artifacts."
read -r -p "Continue? Type yes: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Canceled."
  exit 1
fi

git add .
git restore --staged data/dev/ 2>/dev/null || true

echo
echo "Staged status:"
git status --short
echo

read -r -p "Commit these staged files? Type yes: " COMMIT_CONFIRM

if [ "$COMMIT_CONFIRM" != "yes" ]; then
  echo "Canceled before commit."
  exit 1
fi

git commit -m "phase ${PHASE_NUM}: ${DESC}"
git tag "phase-${PHASE_NUM}-${SLUG}"
git push origin main --tags

echo
echo "Done: phase-${PHASE_NUM}-${SLUG}"
