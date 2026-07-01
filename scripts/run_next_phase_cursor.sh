#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PROMPT_FILE="docs/NEXT_PHASE_PROMPT.md"

echo "RadarArchive - Run Next Phase with Cursor Agent"
echo "Repo: $(pwd)"
echo

if [ ! -f "$PROMPT_FILE" ]; then
  echo "ERROR: Missing $PROMPT_FILE"
  exit 1
fi

echo "Checking Cursor Agent authentication..."
if ! agent status >/dev/null 2>&1; then
  echo
  echo "Cursor Agent does not appear to be authenticated."
  echo
  echo "Run this first:"
  echo "  agent login"
  echo
  echo "Or for API-key/headless use:"
  echo "  export CURSOR_API_KEY=your_key_here"
  echo
  exit 1
fi

echo "Authentication looks OK."
echo

echo "Git status before starting:"
git status --short
echo

if [ -n "$(git status --short)" ]; then
  echo "WARNING: Your repo has uncommitted changes."
  echo
  echo "This may be fine if they are expected runtime artifacts or new scripts,"
  echo "but the agent should not commit unrelated files."
  echo
  echo "Review the status above before continuing."
  echo
  read -r -p "Continue anyway? Type yes to continue: " answer
  if [ "$answer" != "yes" ]; then
    echo "Canceled."
    exit 1
  fi
fi

echo
echo "Starting Cursor Agent with $PROMPT_FILE..."
echo

cursor-agent "$(cat "$PROMPT_FILE")"
