#!/usr/bin/env python3
"""
Update manifest.json based on images in the images/ folder.
- Adds new images with auto-generated titles
- Removes entries for deleted images
- Preserves existing entries and custom titles/dates
"""

import json
import os
from pathlib import Path
from datetime import datetime


def sanitize_filename(filename):
    """Convert filename to title case (e.g., 'my-image.webp' -> 'My Image')"""
    name_without_ext = os.path.splitext(filename)[0]
    # Replace hyphens with spaces and capitalize each word
    return ' '.join(word.capitalize() for word in name_without_ext.split('-'))


def load_manifest(manifest_path):
    """Load existing manifest.json or return empty list"""
    if not os.path.exists(manifest_path):
        return []

    try:
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def get_image_files(images_dir):
    """Get all WebP files in images directory, paired with sibling .mp4 if present.

    Returns a dict {webp_path: video_path_or_None}.
    """
    if not os.path.exists(images_dir):
        return {}

    files = {}
    all_names = set(os.listdir(images_dir))
    for filename in all_names:
        if not filename.endswith('.webp'):
            continue
        stem = filename[:-len('.webp')]
        video_name = f'{stem}.mp4'
        video_path = f'images/{video_name}' if video_name in all_names else None
        files[f'images/{filename}'] = video_path
    return files


def save_manifest(manifest_path, entries):
    """Save manifest.json with sorted entries"""
    # Sort by file path for consistent output
    sorted_entries = sorted(entries, key=lambda x: x['file'])

    with open(manifest_path, 'w') as f:
        json.dump(sorted_entries, f, indent=2)


def update_manifest():
    """Main function to sync manifest with images folder"""
    script_dir = Path(__file__).parent.parent
    images_dir = script_dir / 'images'
    manifest_path = script_dir / 'manifest.json'

    # Load current manifest
    existing_entries = load_manifest(str(manifest_path))
    existing_map = {entry['file']: entry for entry in existing_entries}

    # Get current image files (with optional sibling video)
    current_images = get_image_files(str(images_dir))

    # Build updated entries
    updated_entries = []

    # Keep existing entries for images that still exist, add new ones
    for image_file in sorted(current_images.keys()):
        video_file = current_images[image_file]
        if image_file in existing_map:
            entry = dict(existing_map[image_file])
        else:
            filename = os.path.basename(image_file)
            entry = {
                'file': image_file,
                'title': sanitize_filename(filename),
                'date': datetime.now().strftime('%Y-%m-%d')
            }
        # Sync video field with current state on disk
        if video_file:
            entry['video'] = video_file
        else:
            entry.pop('video', None)
        updated_entries.append(entry)

    # Save updated manifest
    save_manifest(str(manifest_path), updated_entries)

    # Report changes
    old_count = len(existing_entries)
    new_count = len(updated_entries)

    if new_count > old_count:
        print(f"✓ Added {new_count - old_count} new image(s)")
    elif new_count < old_count:
        print(f"✓ Removed {old_count - new_count} image(s)")
    else:
        print("✓ Manifest is up to date")

    print(f"  Total images: {new_count}")


if __name__ == '__main__':
    update_manifest()
