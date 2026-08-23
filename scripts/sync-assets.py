#!/usr/bin/env python3
"""
Reconcile the images/ folder with its derived assets — no ethos source needed.

This is the script behind the everyday workflow: you add or remove files in
images/ directly, then run ./sync.sh. For every still image it makes sure the
two derived files the site needs exist, and it removes derived files whose
source is gone.

Per source image images/<stem>.webp the site needs:
  - images/thumbs/<stem>.webp  600px grid thumbnail (explore/grid.html)
  - images/og/<stem>.jpg       500px JPEG link-preview (explore/share/*.html)

What this script does:
  1. Convert any raw still you dropped in images/ (.jpg/.jpeg/.png/.tif/.tiff/.bmp)
     to a max-1600px WebP, then delete the raw. Filenames are sanitized.
  2. Backfill any missing thumbnail / OG JPEG.
  3. Prune thumbnails / OG JPEGs whose source .webp no longer exists.

It does NOT touch:
  - videos (.mp4) or their posters — those still come from sync-ethos.py
  - images/og-homepage.jpg and images/og-collection.jpg (site-level OG assets)
  - manifest.json / share pages — update-manifest.py and update-share-pages.py
    handle those, and sync.sh runs them right after this.

Usage:
    python3 scripts/sync-assets.py            # backfill + prune
    python3 scripts/sync-assets.py --force    # regenerate every thumb + OG too
"""

import re
import sys
from pathlib import Path

from PIL import Image

IMG_MAX_DIM = 1600
IMG_QUALITY = 82
THUMB_DIM = 600
THUMB_QUALITY = 78
OG_DIM = 500
OG_QUALITY = 78

# Raw still formats we auto-convert to WebP. (HEIC / video need extra tooling.)
RAW_STILL_SUFFIXES = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp'}
# Top-level files that are NOT collection items — never convert or prune these.
KEEP_TOPLEVEL = {'og-homepage.jpg', 'og-collection.jpg'}

REPO = Path(__file__).parent.parent
IMAGES = REPO / 'images'
THUMBS = IMAGES / 'thumbs'
OG = IMAGES / 'og'


def sanitize(stem: str) -> str:
    stem = stem.lower().replace(' ', '-').replace('@', '')
    stem = re.sub(r'[^a-z0-9._-]', '', stem)
    stem = re.sub(r'-+', '-', stem)
    return stem.strip('-') or 'image'


def save_webp(img: Image.Image, dest: Path, max_dim: int, quality: int) -> None:
    img = img.convert('RGB')
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, 'WEBP', quality=quality, method=4)


def save_jpeg(img: Image.Image, dest: Path, max_dim: int, quality: int) -> None:
    img = img.convert('RGB')
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, 'JPEG', quality=quality, optimize=True, progressive=True)


def convert_raw_stills() -> int:
    """Turn dropped raw stills into WebP collection items; delete the raw."""
    converted = 0
    for src in sorted(IMAGES.iterdir()):
        if not src.is_file() or src.name in KEEP_TOPLEVEL:
            continue
        if src.suffix.lower() not in RAW_STILL_SUFFIXES:
            continue
        dest = IMAGES / f'{sanitize(src.stem)}.webp'
        if dest.exists():
            print(f"  SKIP {src.name}: {dest.name} already exists (remove one)")
            continue
        try:
            with Image.open(src) as img:
                save_webp(img, dest, IMG_MAX_DIM, IMG_QUALITY)
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR converting {src.name}: {e}")
            continue
        src.unlink()
        converted += 1
        print(f"  converted {src.name} -> {dest.name}")
    return converted


def sources() -> set[str]:
    """Stems of top-level collection .webp files."""
    return {
        p.stem for p in IMAGES.glob('*.webp')
        if p.is_file() and p.name not in KEEP_TOPLEVEL
    }


def backfill(stems: set[str], force: bool) -> tuple[int, int]:
    made_thumb = made_og = 0
    for stem in sorted(stems):
        src = IMAGES / f'{stem}.webp'
        thumb = THUMBS / f'{stem}.webp'
        og = OG / f'{stem}.jpg'
        if force or not thumb.exists():
            with Image.open(src) as img:
                save_webp(img, thumb, THUMB_DIM, THUMB_QUALITY)
            made_thumb += 1
        if force or not og.exists():
            with Image.open(src) as img:
                save_jpeg(img, og, OG_DIM, OG_QUALITY)
            made_og += 1
    return made_thumb, made_og


def prune(stems: set[str]) -> int:
    pruned = 0
    for thumb in THUMBS.glob('*.webp') if THUMBS.exists() else []:
        if thumb.stem not in stems:
            thumb.unlink()
            pruned += 1
    for og in OG.glob('*.jpg') if OG.exists() else []:
        if og.stem not in stems:
            og.unlink()
            pruned += 1
    return pruned


def main() -> None:
    force = '--force' in sys.argv
    if not IMAGES.exists():
        print(f"No images dir: {IMAGES}")
        return

    converted = convert_raw_stills()
    stems = sources()
    made_thumb, made_og = backfill(stems, force)
    pruned = prune(stems)

    print(f"✓ Assets synced — {len(stems)} images")
    if converted:
        print(f"  Converted {converted} raw still(s) to WebP")
    print(f"  Thumbnails {'regenerated' if force else 'backfilled'}: {made_thumb}")
    print(f"  OG JPEGs {'regenerated' if force else 'backfilled'}: {made_og}")
    if pruned:
        print(f"  Pruned {pruned} orphaned derived file(s)")


if __name__ == '__main__':
    main()
