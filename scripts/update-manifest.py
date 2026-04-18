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
    """Get all WebP files in images directory"""
    if not os.path.exists(images_dir):
        return set()

    webp_files = set()
    for filename in os.listdir(images_dir):
        if filename.endswith('.webp'):
            webp_files.add(f'images/{filename}')
    return webp_files


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

    # Get current image files
    current_images = get_image_files(str(images_dir))

    # Build updated entries
    updated_entries = []

    # Keep existing entries for images that still exist, add new ones
    for image_file in sorted(current_images):
        if image_file in existing_map:
            # Keep existing entry
            updated_entries.append(existing_map[image_file])
        else:
            # Create new entry with auto-generated title
            filename = os.path.basename(image_file)
            new_entry = {
                'file': image_file,
                'title': sanitize_filename(filename),
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            updated_entries.append(new_entry)

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
