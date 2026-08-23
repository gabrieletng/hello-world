#!/usr/bin/env bash
#
# Everyday workflow: you added/removed files in images/, now publish the diff.
#
#   ./sync.sh                 # rebuild derived assets, commit, push, deploy
#   ./sync.sh "my message"    # ...with a custom commit message
#
# Steps, all driven purely by the current contents of images/:
#   1. sync-assets.py        raw stills -> webp; backfill/prune thumbs + og
#   2. update-manifest.py    add/remove manifest.json entries (+ w/h)
#   3. update-share-pages.py add/remove explore/share/*.html
#   4. commit + push -> GitHub Pages redeploys references.gabriele-tangerini.com
#
# images/ is the single source of truth — everything else is derived from it.
set -euo pipefail
cd "$(dirname "$0")"

python3 scripts/sync-assets.py
python3 scripts/update-manifest.py
python3 scripts/update-share-pages.py

git add -A

if git diff --cached --quiet; then
  echo "Nothing to commit — already in sync."
  exit 0
fi

git commit -m "${1:-Sync image collection}"
git push origin main
echo "Pushed. GitHub Pages will redeploy in ~1 min."
