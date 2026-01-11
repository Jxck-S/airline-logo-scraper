import os
import shutil
import hashlib
import argparse
from pathlib import Path
from PIL import Image, ImageChops

# Configuration
SOURCE_MAP = {
    "flightaware_logos": "flightaware_logos",
    "radarbox_banners": "radarbox_banners",
    "radarbox_logos": "radarbox_logos",
    "fr24_logos": "fr24_banners",  # Folder name mismatch handling
    "avcodes_banners": "avcodes_banners"
}

def calculate_md5(file_path):
    """Calculate and return the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        return None

def images_are_visually_identical(file1, file2):
    """Check if two images are visually identical using PIL."""
    try:
        img1 = Image.open(file1)
        img2 = Image.open(file2)
        
        # Must be same mode and dimensions
        if img1.mode != img2.mode or img1.size != img2.size:
            return False
            
        # Compare pixels
        diff = ImageChops.difference(img1, img2)
        if diff.getbbox() is None:
            return True # Identical
        return False
    except Exception:
        return False # Assume different on error (safe fallback)

def sync_folders(source_base, target_base, dry_run=False):
    """Sync files from source folders to target code folders based on map."""
    
    source_base = Path(source_base).resolve()
    target_base = Path(target_base).resolve()

    if not source_base.exists():
        print(f"Error: Source directory {source_base} does not exist.")
        return
    
    if not target_base.exists():
        print(f"Error: Target directory {target_base} does not exist.")
        return

    print(f"Syncing from {source_base} to {target_base}")
    print(f"Dry Run: {'ENABLED' if dry_run else 'DISABLED'}")
    print("-" * 60)

    stats = {"added": 0, "updated": 0, "skipped": 0, "errors": 0}

    for src_dir_name, tgt_dir_name in SOURCE_MAP.items():
        src_dir = source_base / src_dir_name
        tgt_dir = target_base / tgt_dir_name

        if not src_dir.exists():
            print(f"Skipping missing source folder: {src_dir_name}")
            continue

        # Ensure target directory exists
        if not dry_run and not tgt_dir.exists():
            try:
                tgt_dir.mkdir(parents=True, exist_ok=True)
                print(f"Created target directory: {tgt_dir_name}")
            except Exception as e:
                print(f"Error creating directory {tgt_dir_name}: {e}")
                stats["errors"] += 1
                continue

        print(f"\nProcessing {src_dir_name} -> {tgt_dir_name}...")
        
        # Get list of files in source
        files = [f for f in os.listdir(src_dir) if f.lower().endswith('.png')]
        
        for filename in files:
            src_file = src_dir / filename
            tgt_file = tgt_dir / filename

            # Calculate content hash
            src_hash = calculate_md5(src_file)
            
            if not src_hash:
                print(f"Error checking source file {filename}")
                stats["errors"] += 1
                continue

            if not tgt_file.exists():
                # NEW FILE
                print(f"[NEW] {tgt_dir_name}/{filename}")
                if not dry_run:
                    shutil.copy2(src_file, tgt_file)
                stats["added"] += 1
            else:
                # EXISTING FILE - CHECK HASH
                tgt_hash = calculate_md5(tgt_file)
                
                if src_hash != tgt_hash:
                    # Check if visually identical despite hash difference
                    if images_are_visually_identical(src_file, tgt_file):
                        # SKIP - Metadata only change
                        # print(f"[SKIP] {filename} (Visual Match)") # Verbose
                        stats["skipped"] += 1
                    else:
                        # UPDATED FILE - Real visual change
                        src_size = src_file.stat().st_size
                        tgt_size = tgt_file.stat().st_size
                        diff = src_size - tgt_size
                        print(f"[UPD] {tgt_dir_name}/{filename} (Real Diff: {diff:+d}B)")
                        if not dry_run:
                            shutil.copy2(src_file, tgt_file)
                        stats["updated"] += 1
                else:
                    # SAME FILE
                    # print(f"[SKIP] {filename}") # Verbose
                    stats["skipped"] += 1

    print("-" * 60)
    print("Sync Complete.")
    print(f"Added:   {stats['added']}")
    print(f"Updated: {stats['updated']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors:  {stats['errors']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync extracted logos to another repository.")
    parser.add_argument("target", help="Path to the target repository (e.g. ../airline-logos)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    
    args = parser.parse_args()
    
    sync_folders(".", args.target, args.dry_run)
