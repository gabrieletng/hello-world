#!/usr/bin/env python3
"""
Sync ethos/ source media → images/

Images: compressed to WebP (max 1600px, quality 82).
Videos & GIFs: compressed to MP4 (h.264, max 1280px, CRF 28, 64k mono AAC)
plus a WebP poster frame for the grid thumbnail.

Only files this script previously created are removed when their source is gone
(tracked in .ethos-manifest.json — manually added images are never touched).

Usage:
    python3 scripts/sync-ethos.py [ethos_dir]
    ETHOS_DIR=/path/to/ethos python3 scripts/sync-ethos.py
"""

import io
import sys
import re
import os
import json
import shutil
import subprocess
from pathlib import Path
from PIL import Image

VIDEO_SUFFIXES = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.gif'}
SKIP_SUFFIXES = {'.pdf', '.svg'}

IMG_MAX_DIM = 1600
IMG_QUALITY = 82

VIDEO_MAX_W = 1280
VIDEO_CRF = 28
POSTER_AT = 0.5  # seconds into clip for poster frame


def sanitize(name: str) -> str:
    name = name.lower().replace(' ', '-').replace('@', '')
    name = re.sub(r'[^a-z0-9._-]', '', name)
    name = re.sub(r'-+', '-', name)
    return name.strip('-')


def convert_image(src: Path, dest: Path) -> bool:
    try:
        with Image.open(src) as img:
            img = img.convert('RGB')
            img.thumbnail((IMG_MAX_DIM, IMG_MAX_DIM), Image.LANCZOS)
            img.save(dest, 'WEBP', quality=IMG_QUALITY, method=4)
    except Exception as e:
        print(f"  ERROR {src.name}: {e}")
        return False
    return True


def convert_video(src: Path, dest_mp4: Path, dest_poster: Path) -> bool:
    """Compress src video/gif to mp4 and extract a poster webp."""
    try:
        # Compressed mp4 (h.264, scaled, low-bitrate mono audio if present)
        subprocess.run([
            'ffmpeg', '-y', '-loglevel', 'error',
            '-i', str(src),
            '-c:v', 'libx264',
            '-crf', str(VIDEO_CRF),
            '-preset', 'slow',
            '-vf', f"scale='min({VIDEO_MAX_W},iw)':-2",
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            '-c:a', 'aac', '-b:a', '64k', '-ac', '1',
            str(dest_mp4),
        ], check=True)

        # Poster frame from the compressed mp4 — pipe PNG to PIL → WebP
        # (this build of ffmpeg doesn't ship libwebp encoder)
        result = subprocess.run([
            'ffmpeg', '-loglevel', 'error',
            '-ss', str(POSTER_AT),
            '-i', str(dest_mp4),
            '-frames:v', '1',
            '-vf', f"scale='min({IMG_MAX_DIM},iw)':-2",
            '-f', 'image2pipe', '-vcodec', 'png', '-',
        ], check=True, capture_output=True)
        with Image.open(io.BytesIO(result.stdout)) as poster:
            poster.convert('RGB').save(dest_poster, 'WEBP', quality=IMG_QUALITY, method=4)
    except subprocess.CalledProcessError as e:
        print(f"  ERROR {src.name}: ffmpeg failed ({e.returncode})")
        if dest_mp4.exists(): dest_mp4.unlink()
        if dest_poster.exists(): dest_poster.unlink()
        return False
    return True


def load_ethos_manifest(path: Path) -> set:
    if path.exists():
        return set(json.loads(path.read_text()))
    return set()


def save_ethos_manifest(path: Path, stems: set):
    path.write_text(json.dumps(sorted(stems), indent=2) + '\n')


def main():
    if not shutil.which('ffmpeg'):
        print("ffmpeg not found on PATH — install it (`brew install ffmpeg`) before syncing videos.")
        sys.exit(1)

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

    ethos_manifest_path = repo_root / '.ethos-manifest.json'
    owned_stems = load_ethos_manifest(ethos_manifest_path)

    # Build expected stems → (kind, source) from current ethos sources
    expected: dict[str, tuple[str, Path]] = {}
    for f in sorted(ethos_dir.iterdir()):
        if not f.is_file() or f.suffix.lower() in SKIP_SUFFIXES:
            continue
        stem = sanitize(f.stem)
        kind = 'video' if f.suffix.lower() in VIDEO_SUFFIXES else 'image'
        expected[stem] = (kind, f)

    added = errors = 0
    for stem, (kind, src) in expected.items():
        webp = images_dir / f"{stem}.webp"
        mp4 = images_dir / f"{stem}.mp4"

        if kind == 'image':
            if webp.exists():
                owned_stems.add(stem)
                continue
            print(f"+ {webp.name}  ", end='', flush=True)
            if convert_image(src, webp):
                before, after = src.stat().st_size, webp.stat().st_size
                print(f"{before // 1024}KB → {after // 1024}KB")
                owned_stems.add(stem)
                added += 1
            else:
                errors += 1
        else:
            # Video: needs both mp4 and poster webp
            if webp.exists() and mp4.exists():
                owned_stems.add(stem)
                continue
            print(f"+ {mp4.name} (+ poster)  ", end='', flush=True)
            if convert_video(src, mp4, webp):
                before = src.stat().st_size
                after = mp4.stat().st_size + webp.stat().st_size
                print(f"{before // 1024}KB → {after // 1024}KB")
                owned_stems.add(stem)
                added += 1
            else:
                errors += 1

    # Remove orphans (files this script previously created whose source is gone)
    removed = 0
    for stem in sorted(owned_stems - set(expected.keys())):
        for ext in ('.webp', '.mp4'):
            artifact = images_dir / f"{stem}{ext}"
            if artifact.exists():
                print(f"- {artifact.name}")
                artifact.unlink()
                removed += 1
        owned_stems.discard(stem)

    save_ethos_manifest(ethos_manifest_path, owned_stems)

    print(f"\nSync done.  Added: {added}  Removed: {removed}  Errors: {errors}")


if __name__ == '__main__':
    main()
