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

if command -v agent >/dev/null 2>&1; then
  AGENT_BIN="agent"
elif command -v agent >/dev/null 2>&1; then
  AGENT_BIN="agent"
else
  echo "ERROR: neither agent nor agent was found."
  echo
  echo "Try opening Cursor and installing/enabling the Cursor CLI."
  echo "Then verify with:"
  echo "  agent status"
  echo "  agent --help"
  exit 1
fi

echo "Using agent command: $AGENT_BIN"
echo

echo "Checking Cursor Agent authentication..."
if ! agent status >/dev/null 2>&1; then
  echo "ERROR: Cursor Agent is not authenticated."
  echo "Run:"
  echo "  agent login"
  exit 1
fi

echo "Authentication looks OK."
echo

echo "Git status before starting:"
git status --short
echo

if [ -n "$(git status --short)" ]; then
  if [ "${CURSOR_AGENT_ALLOW_DIRTY:-0}" != "1" ]; then
    echo "ERROR: Repo has uncommitted changes."
    echo
    echo "Clean, commit, or intentionally allow dirty state with:"
    echo "  CURSOR_AGENT_ALLOW_DIRTY=1 ./scripts/run_next_phase_cursor.sh"
    echo
    echo "Current uncommitted files are listed above."
    exit 1
  fi
fi

echo "Starting Cursor Agent with $PROMPT_FILE..."
echo

if [ "${CURSOR_AGENT_FORCE:-0}" = "1" ]; then
  echo "Force mode enabled."
  "$AGENT_BIN" --trust -f "$(cat "$PROMPT_FILE")"
else
  echo "Interactive trusted mode."
  "$AGENT_BIN" --trust "$(cat "$PROMPT_FILE")"
fi
