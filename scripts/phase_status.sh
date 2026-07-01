#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Repo:"
pwd
echo

echo "Current branch:"
git branch --show-current
echo

echo "Git status:"
git status --short
echo

echo "Latest commits:"
git log --oneline --decorate -8
echo

echo "Latest tags:"
git tag --sort=-creatordate | head -8
