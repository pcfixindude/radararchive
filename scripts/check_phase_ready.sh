#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Project:"
pwd
echo

echo "Git status:"
git status --short
echo

echo "Next phase prompt:"
echo "------------------"
if [ -f docs/NEXT_PHASE_PROMPT.md ]; then
  sed -n '1,160p' docs/NEXT_PHASE_PROMPT.md
else
  echo "Missing docs/NEXT_PHASE_PROMPT.md"
  exit 1
fi
