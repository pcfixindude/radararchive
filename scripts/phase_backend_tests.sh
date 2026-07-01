#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Running backend/full project tests..."
make test
