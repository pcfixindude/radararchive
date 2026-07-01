#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "This will discard local changes under data/dev/ only."
echo
git status --short data/dev/ || true
echo

read -r -p "Clean data/dev runtime artifacts? Type yes: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Canceled."
  exit 1
fi

git restore data/dev/ 2>/dev/null || true

echo
echo "Done. Current status:"
git status --short
