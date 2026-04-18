#!/usr/bin/env python3
"""
Generate grid thumbnails at images/thumbs/<name>.webp.

Thumbs are smaller than the full-res files so the grid loads fast and
decodes cheap on pan/zoom. The lightbox still uses the full-res file.

Usage:
    python3 scripts/make-thumbnails.py          # backfill missing + prune orphans
    python3 scripts/make-thumbnails.py --force  # regenerate every thumb
"""

import sys
from pathlib import Path
from PIL import Image

THUMB_DIM = 600     # max width/height in px — see PROJECT notes on zoom/crispness tradeoff
THUMB_QUALITY = 78


def make_thumb(src: Path, dest: Path) -> bool:
    try:
        with Image.open(src) as img:
            img = img.convert('RGB')
            img.thumbnail((THUMB_DIM, THUMB_DIM), Image.LANCZOS)
            dest.parent.mkdir(parents=True, exist_ok=True)
            img.save(dest, 'WEBP', quality=THUMB_QUALITY, method=4)
    except Exception as e:
        print(f"  ERROR {src.name}: {e}")
        return False
    return True


def main():
    force = '--force' in sys.argv
    repo_root = Path(__file__).parent.parent
    images_dir = repo_root / 'images'
    thumbs_dir = images_dir / 'thumbs'
    thumbs_dir.mkdir(exist_ok=True)

    if not images_dir.exists():
        print(f"No images dir: {images_dir}")
        return

    sources = {f for f in images_dir.iterdir() if f.is_file() and f.suffix.lower() == '.webp'}

    added = regen = skipped = errors = 0
    for src in sorted(sources):
        thumb = thumbs_dir / src.name
        if thumb.exists() and not force:
            skipped += 1
            continue
        ok = make_thumb(src, thumb)
        if ok:
            if thumb.exists() and not force:
                added += 1
            else:
                regen += 1 if force else 0
                added += 0 if force else 1
        else:
            errors += 1

    # Remove orphan thumbs whose source is gone
    removed = 0
    source_names = {f.name for f in sources}
    for thumb in sorted(thumbs_dir.iterdir()):
        if thumb.is_file() and thumb.suffix.lower() == '.webp' and thumb.name not in source_names:
            print(f"- thumbs/{thumb.name}")
            thumb.unlink()
            removed += 1

    label = "Regenerated" if force else "Added"
    print(f"\n{label}: {added}  Skipped: {skipped}  Removed: {removed}  Errors: {errors}")


if __name__ == '__main__':
    main()
