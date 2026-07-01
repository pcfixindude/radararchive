#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PROMPT_FILE="docs/NEXT_PHASE_PROMPT.md"
LOG_DIR="data/dev/agent_logs"
mkdir -p "$LOG_DIR"

START_TS="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="$LOG_DIR/auto_phase_${START_TS}.log"

echo "RadarArchive - Full Auto Phase"
echo "Repo: $(pwd)"
echo "Log: $LOG_FILE"
echo

if [ ! -f "$PROMPT_FILE" ]; then
  echo "ERROR: Missing $PROMPT_FILE"
  exit 1
fi

if ! command -v agent >/dev/null 2>&1; then
  echo "ERROR: Cursor Agent CLI command 'agent' was not found."
  echo "Install with:"
  echo "  curl https://cursor.com/install -fsS | bash"
  exit 1
fi

if ! agent status >/dev/null 2>&1; then
  echo "ERROR: Cursor Agent is not authenticated."
  echo "Run:"
  echo "  agent login"
  exit 1
fi

echo "Checking for clean repo before starting..."
if [ -n "$(git status --short)" ]; then
  echo "ERROR: Repo is not clean before starting."
  echo
  git status --short
  echo
  echo "Finish, commit, restore, or clean these changes before running auto phase."
  exit 1
fi

echo "Repo is clean."
echo

echo "Running Cursor Agent in full auto force mode..."
echo

set +e
agent -p --trust -f "$(cat "$PROMPT_FILE")" | tee "$LOG_FILE"
AGENT_EXIT=${PIPESTATUS[0]}
set -e

if [ "$AGENT_EXIT" -ne 0 ]; then
  echo
  echo "ERROR: Cursor Agent failed with exit code $AGENT_EXIT"
  echo "Log: $LOG_FILE"
  exit "$AGENT_EXIT"
fi

echo
echo "Cursor Agent finished."
echo

echo "Status after agent:"
git status --short
echo

if [ -z "$(git status --short)" ]; then
  echo "No changes were made. Nothing to commit."
  exit 0
fi

echo "Running backend/full project tests..."
make test

echo
echo "Running frontend tests and build..."
cd frontend
npm test
npm run build
cd ..

echo
echo "Cleaning runtime artifacts under data/dev..."
git restore data/dev/ 2>/dev/null || true

echo
echo "Detecting phase number and title..."

PHASE_LINE="$(
  {
    grep -Eho 'Phase [0-9]+[[:space:]]*[-—:][[:space:]].*' docs/CHATGPT_REVIEW.md 2>/dev/null || true
    grep -Eho 'Phase [0-9]+[[:space:]]*[-—:][[:space:]].*' docs/PHASE_LOG.md 2>/dev/null || true
    grep -Eho 'Phase [0-9]+[[:space:]]*[-—:][[:space:]].*' "$LOG_FILE" 2>/dev/null || true
  } | tail -1
)"

if [ -z "$PHASE_LINE" ]; then
  echo "ERROR: Could not auto-detect phase line."
  echo "Expected something like:"
  echo "  Phase 125 — some title"
  echo
  echo "Commit manually or update docs/CHATGPT_REVIEW.md with the phase heading."
  exit 1
fi

PHASE_NUM="$(echo "$PHASE_LINE" | sed -E 's/.*Phase ([0-9]+).*/\1/')"
PHASE_TITLE="$(echo "$PHASE_LINE" | sed -E 's/.*Phase [0-9]+[[:space:]]*[-—:][[:space:]]*//')"

if [ -z "$PHASE_NUM" ] || [ -z "$PHASE_TITLE" ]; then
  echo "ERROR: Failed to parse phase number/title from:"
  echo "$PHASE_LINE"
  exit 1
fi

SLUG="$(
  echo "$PHASE_TITLE" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
)"

COMMIT_MSG="phase ${PHASE_NUM}: ${PHASE_TITLE}"
TAG_NAME="phase-${PHASE_NUM}-${SLUG}"

echo "Detected:"
echo "  Phase: $PHASE_NUM"
echo "  Title: $PHASE_TITLE"
echo "  Commit: $COMMIT_MSG"
echo "  Tag: $TAG_NAME"
echo

echo "Staging files, excluding data/dev runtime artifacts..."
git add .
git restore --staged data/dev/ 2>/dev/null || true

echo
echo "Final staged status:"
git status --short
echo

if [ -z "$(git diff --cached --name-only)" ]; then
  echo "ERROR: No staged files to commit."
  exit 1
fi

echo "Committing..."
git commit -m "$COMMIT_MSG"

echo "Tagging..."
git tag "$TAG_NAME"

echo "Pushing..."
git push origin main --tags

echo
echo "Auto phase complete."
echo "Commit: $COMMIT_MSG"
echo "Tag: $TAG_NAME"
echo

echo "Final status:"
git status --short
