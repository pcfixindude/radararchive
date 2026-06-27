#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="${1:-$HOME/Projects/radararchive}"
mkdir -p "$PROJECT_DIR"
echo "This script is a placeholder because the ZIP scaffold already contains the full project."
echo "Unzip radararchive_scaffold.zip, then run:"
echo "  cd radararchive"
echo "  make setup"
echo "  make test"
echo "  make backend"
echo "In a second terminal: make frontend"
