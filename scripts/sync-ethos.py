#!/usr/bin/env python3
"""
Sync ethos/ source images → images/
- Compresses new images to WebP
- Removes WebP files whose source no longer exists in ethos
- Skips videos

Usage:
    python3 scripts/sync-ethos.py [ethos_dir]
    ETHOS_DIR=/path/to/ethos python3 scripts/sync-ethos.py
"""

import sys
import re
import os
from pathlib import Path
from PIL import Image

SKIP_SUFFIXES = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.gif', '.pdf', '.svg'}
MAX_DIM = 1600
QUALITY = 82


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
    images_dir.mkdir(exist_ok=True)

    # Build expected webp stems from ethos sources
    expected: dict[str, Path] = {}
    for f in sorted(ethos_dir.iterdir()):
        if not f.is_file() or f.suffix.lower() in SKIP_SUFFIXES:
            continue
        stem = sanitize(f.stem)
        expected[stem] = f

    # Add new images
    added = errors = 0
    for stem, src in expected.items():
        out = images_dir / f"{stem}.webp"
        if out.exists():
            continue
        print(f"+ {out.name}  ", end='', flush=True)
        if convert(src, out):
            before, after = src.stat().st_size, out.stat().st_size
            print(f"{before // 1024}KB → {after // 1024}KB")
            added += 1
        else:
            errors += 1

    # Remove orphaned webps
    removed = 0
    for webp in sorted(images_dir.glob('*.webp')):
        if webp.stem not in expected:
            print(f"- {webp.name}")
            webp.unlink()
            removed += 1

    print(f"\nSync done.  Added: {added}  Removed: {removed}  Errors: {errors}")


if __name__ == '__main__':
    main()
