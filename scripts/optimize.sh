#!/usr/bin/env bash
# Convert images to WebP and add them to images/.
# Skips videos. Skips files already present as .webp.
#
# Usage:
#   ./scripts/optimize.sh <source_dir>        # batch from external folder
#   ./scripts/optimize.sh images/             # re-compress existing images in-place

set -euo pipefail

SRC="${1:?Usage: $0 <source_dir>}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$REPO_ROOT/images"
MAX=1600
QUALITY=82

mkdir -p "$DEST"

count=0
skipped=0

while IFS= read -r -d '' f; do
  [[ -f "$f" ]] || continue

  ext="${f##*.}"
  ext_lower="${ext,,}"

  # Skip videos and non-image files
  case "$ext_lower" in
    mp4|mov|avi|mkv|webm|gif|pdf|svg) continue ;;
  esac

  # Skip if already a webp being re-processed into itself
  base_raw="$(basename "$f")"
  base="${base_raw%.*}"
  base="${base,,}"
  base="${base// /-}"
  base="${base//@/}"
  base="${base//[^a-z0-9._-]/}"
  base="${base//--/-}"
  base="${base#-}"; base="${base%-}"

  out="$DEST/${base}.webp"

  # Skip if output already exists (unless source is itself the .webp we'd overwrite)
  if [[ -f "$out" && "$f" != "$out" ]]; then
    echo "skip (exists): ${base}.webp"
    ((skipped++)) || true
    continue
  fi

  echo "→ ${base}.webp"
  ffmpeg -hide_banner -loglevel error -y -i "$f" \
    -vf "scale=w=${MAX}:h=${MAX}:force_original_aspect_ratio=decrease" \
    -quality "$QUALITY" \
    "$out"
  ((count++)) || true

done < <(find "$SRC" -maxdepth 1 -type f -print0 | sort -z)

echo ""
echo "Done. Converted: $count  Skipped: $skipped"
