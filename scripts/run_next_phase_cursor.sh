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

if ! command -v cursor-agent >/dev/null 2>&1; then
  echo "ERROR: cursor-agent command not found."
  echo "Open Cursor and install/enable the Cursor CLI, then try again."
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
  echo "Review the status above before continuing."
  echo "The agent should not commit unrelated runtime artifacts."
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

if [ "${CURSOR_AGENT_FORCE:-0}" = "1" ]; then
  echo "Force mode enabled: cursor-agent --trust -f"
  cursor-agent --trust -f "$(cat "$PROMPT_FILE")"
else
  echo "Interactive mode: cursor-agent --trust"
  cursor-agent --trust "$(cat "$PROMPT_FILE")"
fi
