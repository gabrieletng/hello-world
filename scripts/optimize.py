#!/usr/bin/env python3
"""
Convert images to WebP and output them to images/.
Skips videos and files already present as .webp.

Usage:
    python3 scripts/optimize.py <source_dir>
    python3 scripts/optimize.py images/    # re-compress existing images
"""

import sys
import re
from pathlib import Path
from PIL import Image

SKIP_SUFFIXES = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.gif', '.pdf', '.svg'}
MAX_DIM = 1600
QUALITY = 82

def sanitize(name: str) -> str:
    name = name.lower()
    name = name.replace(' ', '-').replace('@', '')
    name = re.sub(r'[^a-z0-9._-]', '', name)
    name = re.sub(r'-+', '-', name)
    return name.strip('-')

def convert(src: Path, dest: Path):
    try:
        with Image.open(src) as img:
            img = img.convert('RGB')
            img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
            img.save(dest, 'WEBP', quality=QUALITY, method=4)
    except Exception as e:
        print(f"  ERROR: {e}")
        return False
    return True

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    src_dir = Path(sys.argv[1]).resolve()

    # Handle missing source directory gracefully
    if not src_dir.exists():
        print(f"Source directory does not exist: {src_dir}")
        return

    if not src_dir.is_dir():
        print(f"Source path is not a directory: {src_dir}")
        return

    repo_root = Path(__file__).parent.parent
    dest_dir = repo_root / 'images'
    dest_dir.mkdir(exist_ok=True)

    try:
        files = sorted(f for f in src_dir.iterdir() if f.is_file())
    except PermissionError:
        print(f"Permission denied reading directory: {src_dir}")
        return
    converted = skipped = errors = 0

    for f in files:
        if f.suffix.lower() in SKIP_SUFFIXES:
            continue

        stem = sanitize(f.stem)
        out = dest_dir / f"{stem}.webp"

        if out.exists() and f != out:
            print(f"skip (exists): {out.name}")
            skipped += 1
            continue

        print(f"→ {out.name}", end='  ', flush=True)
        ok = convert(f, out)
        if ok:
            before = f.stat().st_size
            after = out.stat().st_size
            print(f"{before//1024}KB → {after//1024}KB")
            converted += 1
        else:
            errors += 1

    print(f"\nDone. Converted: {converted}  Skipped: {skipped}  Errors: {errors}")

if __name__ == '__main__':
    main()
