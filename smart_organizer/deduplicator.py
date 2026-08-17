"""
Duplicate File Detector for Smart File Organizer.

Uses SHA-256 (or MD5) content hashing to identify duplicate files,
reports space recoverable, and supports safe dry-run deletion.
"""

import hashlib
import logging
from collections import defaultdict
from pathlib import Path
from typing import Optional

from .utils import format_size, get_file_date, print_banner, print_table

logger = logging.getLogger("smart_organizer.deduplicator")


def hash_file(file_path: Path, algorithm: str = "sha256", chunk_size: int = 8192) -> str:
    """
    Compute the hash of a file's contents.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm ('sha256' or 'md5').
        chunk_size: Size of chunks to read at a time.

    Returns:
        Hex digest string of the file hash.
    """
    hasher = hashlib.new(algorithm)

    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
    except (OSError, PermissionError) as e:
        logger.error(f"Cannot read file for hashing: {file_path} - {e}")
        return ""

    return hasher.hexdigest()


def find_duplicates(
    file_list: list,
    algorithm: str = "sha256",
) -> dict[str, list[Path]]:
    """
    Find duplicate files by content hash.

    Args:
        file_list: List of FileInfo objects or Path objects.
        algorithm: Hash algorithm to use.

    Returns:
        Dictionary mapping hash -> list of duplicate file paths.
        Only includes hashes with 2+ files.
    """
    hash_map: dict[str, list[Path]] = defaultdict(list)
    total = len(file_list)

    logger.info(f"Hashing {total} files for duplicate detection (algorithm: {algorithm})...")

    for i, file_item in enumerate(file_list, 1):
        # Support both FileInfo objects and Path objects
        file_path = getattr(file_item, "path", file_item)

        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        if not file_path.is_file():
            continue

        file_hash = hash_file(file_path, algorithm)
        if file_hash:
            hash_map[file_hash].append(file_path)

        # Log progress every 50 files
        if i % 50 == 0 or i == total:
            logger.debug(f"Hashed {i}/{total} files ({i*100//total}%)")

    # Filter to only duplicates (2+ files with same hash)
    duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}

    total_dupes = sum(len(paths) - 1 for paths in duplicates.values())
    logger.info(f"Found {len(duplicates)} duplicate groups ({total_dupes} duplicate files)")

    return duplicates


def get_duplicate_summary(duplicates: dict[str, list[Path]]) -> dict:
    """
    Generate a summary of duplicate detection results.

    Args:
        duplicates: Dictionary from find_duplicates.

    Returns:
        Summary dictionary with stats and details.
    """
    if not duplicates:
        return {
            "total_duplicate_groups": 0,
            "total_duplicate_files": 0,
            "total_space_recoverable": 0,
            "total_space_recoverable_human": "0 B",
            "details": [],
        }

    total_duplicate_files = 0
    total_space_recoverable = 0
    details = []

    for file_hash, paths in duplicates.items():
        # The first file is the original, rest are duplicates
        file_size = 0
        try:
            file_size = paths[0].stat().st_size
        except OSError:
            pass

        duplicate_count = len(paths) - 1
        space_recoverable = file_size * duplicate_count
        total_duplicate_files += duplicate_count
        total_space_recoverable += space_recoverable

        details.append({
            "hash": file_hash[:16] + "...",
            "file_size": file_size,
            "file_size_human": format_size(file_size),
            "total_copies": len(paths),
            "duplicate_count": duplicate_count,
            "space_recoverable": format_size(space_recoverable),
            "files": [str(p) for p in paths],
        })

    return {
        "total_duplicate_groups": len(duplicates),
        "total_duplicate_files": total_duplicate_files,
        "total_space_recoverable": total_space_recoverable,
        "total_space_recoverable_human": format_size(total_space_recoverable),
        "details": details,
    }


def remove_duplicates(
    duplicates: dict[str, list[Path]],
    dry_run: bool = True,
    keep: str = "oldest",
) -> list[Path]:
    """
    Remove duplicate files, keeping one copy.

    Args:
        duplicates: Dictionary from find_duplicates.
        dry_run: If True, only report what would be deleted.
        keep: Strategy for which file to keep ('oldest' or 'newest').

    Returns:
        List of file paths that were (or would be) deleted.
    """
    deleted_files: list[Path] = []

    for file_hash, paths in duplicates.items():
        # Sort by modification date
        try:
            sorted_paths = sorted(paths, key=lambda p: get_file_date(p))
        except Exception:
            sorted_paths = paths

        if keep == "newest":
            keep_file = sorted_paths[-1]
            remove_files = sorted_paths[:-1]
        else:  # oldest
            keep_file = sorted_paths[0]
            remove_files = sorted_paths[1:]

        logger.info(f"Keeping: {keep_file.name}")

        for dup_file in remove_files:
            if dry_run:
                logger.info(f"  [DRY RUN] Would delete: {dup_file}")
                deleted_files.append(dup_file)
            else:
                try:
                    file_size = dup_file.stat().st_size
                    dup_file.unlink()
                    deleted_files.append(dup_file)
                    logger.info(f"  Deleted: {dup_file} ({format_size(file_size)})")
                except (OSError, PermissionError) as e:
                    logger.error(f"  Failed to delete {dup_file}: {e}")

    return deleted_files


def print_duplicate_report(duplicates: dict[str, list[Path]], summary: dict) -> None:
    """
    Pretty-print duplicate detection results to console.

    Args:
        duplicates: Dictionary from find_duplicates.
        summary: Summary dictionary from get_duplicate_summary.
    """
    print_banner("DUPLICATE DETECTION RESULTS")

    print(f"  [SEARCH] Duplicate Groups:   {summary['total_duplicate_groups']}")
    print(f"  [FILES]  Duplicate Files:    {summary['total_duplicate_files']}")
    print(f"  [SIZE]   Space Recoverable:  {summary['total_space_recoverable_human']}")

    if summary["details"]:
        print(f"\n  {'-' * 55}")
        print(f"  DUPLICATE GROUPS")
        print(f"  {'-' * 55}")

        for i, group in enumerate(summary["details"], 1):
            print(f"\n  Group {i} | Size: {group['file_size_human']} | "
                  f"Copies: {group['total_copies']} | "
                  f"Recoverable: {group['space_recoverable']}")
            print(f"  Hash: {group['hash']}")
            for j, file_path in enumerate(group["files"]):
                marker = "  [KEEP]  " if j == 0 else "  [DUPE]  "
                print(f"    {marker} {file_path}")

    print()
