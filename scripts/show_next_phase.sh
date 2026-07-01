#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f docs/NEXT_PHASE_PROMPT.md ]; then
  echo "Missing docs/NEXT_PHASE_PROMPT.md"
  exit 1
fi

cat docs/NEXT_PHASE_PROMPT.md
