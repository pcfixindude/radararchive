#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../frontend"

echo "Running frontend tests..."
npm test

echo
echo "Running frontend build..."
npm run build
