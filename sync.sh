#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 scripts/sync-ethos.py
python3 scripts/update-manifest.py

git add images/ manifest.json .ethos-manifest.json

if git diff --cached --quiet; then
  echo "Nothing new to commit."
else
  git commit -m "${1:-new image sync}"
  git push origin main
fi
