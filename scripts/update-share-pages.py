#!/usr/bin/env python3
"""
Generate a static share page per item in explore/share/{stem}.html.

Each page carries og:image and Twitter Card meta tags so link previews
in messengers and social apps show the item's image. Humans who open
the link are redirected to explore/grid.html?image=... via meta refresh
and a JS fallback.

Run as part of sync.sh (after update-manifest.py). Idempotent:
- Creates missing pages
- Removes pages whose image is no longer in manifest.json
- Skips rewriting unchanged pages to avoid git churn
"""

import html
import json
from pathlib import Path

BASE_URL = 'https://gabrieletng.github.io/hello-world'
SUBTITLE = 'A Story of Love and Death'

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — {subtitle}</title>

<meta property="og:type" content="website">
<meta property="og:title" content="{title} — {subtitle}">
<meta property="og:description" content="{subtitle}">
<meta property="og:url" content="{share_url}">
<meta property="og:image" content="{image_url}">
<meta property="og:image:type" content="image/webp">
{og_dims}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title} — {subtitle}">
<meta name="twitter:image" content="{image_url}">

<link rel="canonical" href="{redirect_url}">
<meta http-equiv="refresh" content="0; url={redirect_url}">
<style>body{{font-family:system-ui,sans-serif;margin:2rem;color:#666}}</style>
</head>
<body>
<script>location.replace({redirect_js});</script>
<p>Redirecting to <a href="{redirect_url}">{title}</a>…</p>
</body>
</html>
"""


def stem_for(file_path: str) -> str:
    return Path(file_path).stem


def render_page(entry: dict) -> str:
    stem = stem_for(entry['file'])
    title = entry.get('title') or stem
    image_url = f"{BASE_URL}/{entry['file']}"
    share_url = f"{BASE_URL}/explore/share/{stem}.html"
    redirect_url = f"{BASE_URL}/explore/grid.html?image={entry['file']}"

    if entry.get('w') and entry.get('h'):
        og_dims = (
            f'<meta property="og:image:width" content="{entry["w"]}">\n'
            f'<meta property="og:image:height" content="{entry["h"]}">\n'
        )
    else:
        og_dims = ''

    return TEMPLATE.format(
        title=html.escape(title, quote=True),
        subtitle=SUBTITLE,
        share_url=html.escape(share_url, quote=True),
        image_url=html.escape(image_url, quote=True),
        redirect_url=html.escape(redirect_url, quote=True),
        redirect_js=json.dumps(redirect_url),
        og_dims=og_dims,
    )


def main():
    repo_root = Path(__file__).parent.parent
    manifest_path = repo_root / 'manifest.json'
    share_dir = repo_root / 'explore' / 'share'
    share_dir.mkdir(parents=True, exist_ok=True)

    entries = json.loads(manifest_path.read_text())
    expected = {f"{stem_for(e['file'])}.html" for e in entries}

    written = unchanged = 0
    for entry in entries:
        page_path = share_dir / f"{stem_for(entry['file'])}.html"
        new_content = render_page(entry)
        if page_path.exists() and page_path.read_text() == new_content:
            unchanged += 1
        else:
            page_path.write_text(new_content)
            written += 1

    removed = 0
    for existing in share_dir.iterdir():
        if existing.is_file() and existing.suffix == '.html' and existing.name not in expected:
            existing.unlink()
            removed += 1

    print(f"✓ Share pages: {written} written, {unchanged} unchanged, {removed} removed")


if __name__ == '__main__':
    main()
