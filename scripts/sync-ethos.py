#!/usr/bin/env python3
"""
Sync ethos/ source images → images/
- Compresses new images to WebP
- Removes only WebP files that were previously created by this script
  (tracked in .ethos-manifest.json — manually added images are never touched)
- Skips videos

Usage:
    python3 scripts/sync-ethos.py [ethos_dir]
    ETHOS_DIR=/path/to/ethos python3 scripts/sync-ethos.py
"""

import sys
import re
import os
import json
from pathlib import Path
from PIL import Image

SKIP_SUFFIXES = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.gif', '.pdf', '.svg'}
MAX_DIM = 1600
QUALITY = 82
THUMB_DIM = 600            # grid-view thumbnail size — full-res still used by lightbox
THUMB_QUALITY = 78


def sanitize(name: str) -> str:
    name = name.lower().replace(' ', '-').replace('@', '')
    name = re.sub(r'[^a-z0-9._-]', '', name)
    name = re.sub(r'-+', '-', name)
    return name.strip('-')


def convert(src: Path, dest: Path) -> bool:
    try:
        with Image.open(src) as img:
            img = img.convert('RGB')
            img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
            img.save(dest, 'WEBP', quality=QUALITY, method=4)
    except Exception as e:
        print(f"  ERROR {src.name}: {e}")
        return False
    return True


def make_thumb(src: Path, dest: Path) -> bool:
    try:
        with Image.open(src) as img:
            img = img.convert('RGB')
            img.thumbnail((THUMB_DIM, THUMB_DIM), Image.LANCZOS)
            dest.parent.mkdir(parents=True, exist_ok=True)
            img.save(dest, 'WEBP', quality=THUMB_QUALITY, method=4)
    except Exception as e:
        print(f"  THUMB ERROR {src.name}: {e}")
        return False
    return True


def load_ethos_manifest(path: Path) -> set:
    if path.exists():
        return set(json.loads(path.read_text()))
    return set()


def save_ethos_manifest(path: Path, stems: set):
    path.write_text(json.dumps(sorted(stems), indent=2) + '\n')


def main():
    repo_root = Path(__file__).parent.parent

    if len(sys.argv) > 1:
        ethos_dir = Path(sys.argv[1]).resolve()
    elif 'ETHOS_DIR' in os.environ:
        ethos_dir = Path(os.environ['ETHOS_DIR']).resolve()
    else:
        ethos_dir = (repo_root / '../ethos').resolve()

    if not ethos_dir.exists():
        print(f"ethos dir not found: {ethos_dir} — skipping sync")
        return

    images_dir = repo_root / 'images'
    thumbs_dir = images_dir / 'thumbs'
    images_dir.mkdir(exist_ok=True)
    thumbs_dir.mkdir(exist_ok=True)

    # .ethos-manifest.json tracks which webp stems this script owns
    ethos_manifest_path = repo_root / '.ethos-manifest.json'
    owned_stems = load_ethos_manifest(ethos_manifest_path)

    # Build expected webp stems from current ethos sources
    expected: dict[str, Path] = {}
    for f in sorted(ethos_dir.iterdir()):
        if not f.is_file() or f.suffix.lower() in SKIP_SUFFIXES:
            continue
        stem = sanitize(f.stem)
        expected[stem] = f

    # Add new images (full-res + thumb)
    added = errors = 0
    for stem, src in expected.items():
        out = images_dir / f"{stem}.webp"
        thumb = thumbs_dir / f"{stem}.webp"
        if out.exists():
            owned_stems.add(stem)  # claim ownership of pre-existing ethos files
            if not thumb.exists():
                make_thumb(out, thumb)     # backfill thumb if someone deleted it
            continue
        print(f"+ {out.name}  ", end='', flush=True)
        if convert(src, out):
            before, after = src.stat().st_size, out.stat().st_size
            print(f"{before // 1024}KB → {after // 1024}KB")
            make_thumb(out, thumb)
            owned_stems.add(stem)
            added += 1
        else:
            errors += 1

    # Remove only orphans that this script previously created (full-res + thumb)
    removed = 0
    for stem in sorted(owned_stems - set(expected.keys())):
        webp = images_dir / f"{stem}.webp"
        thumb = thumbs_dir / f"{stem}.webp"
        if webp.exists():
            print(f"- {webp.name}")
            webp.unlink()
            removed += 1
        if thumb.exists():
            thumb.unlink()
        owned_stems.discard(stem)

    # Persist updated ownership list
    save_ethos_manifest(ethos_manifest_path, owned_stems)

    print(f"\nSync done.  Added: {added}  Removed: {removed}  Errors: {errors}")


if __name__ == '__main__':
    main()
