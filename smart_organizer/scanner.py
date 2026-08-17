"""
File Scanner Module for Smart File Organizer.

Recursively scans directories, classifies files by extension into
categories, and collects detailed metadata for each file found.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import get_category, load_config
from .utils import format_size, get_file_date, get_file_created_date, print_banner, print_table

logger = logging.getLogger("smart_organizer.scanner")


@dataclass
class FileInfo:
    """Data class representing scanned file information."""
    path: Path
    name: str
    extension: str
    category: str
    size: int
    size_human: str
    created: datetime
    modified: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "path": str(self.path),
            "name": self.name,
            "extension": self.extension,
            "category": self.category,
            "size": self.size,
            "size_human": self.size_human,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
        }


def scan_directory(
    target_path: str | Path,
    config: Optional[dict] = None,
    recursive: bool = True,
) -> list[FileInfo]:
    """
    Scan a directory and classify all files found.

    Args:
        target_path: Path to the directory to scan.
        config: Configuration dictionary. Loads defaults if None.
        recursive: If True, scan subdirectories recursively.

    Returns:
        List of FileInfo objects for each file found.

    Raises:
        FileNotFoundError: If target_path doesn't exist.
        NotADirectoryError: If target_path is not a directory.
    """
    target = Path(target_path).resolve()

    if not target.exists():
        raise FileNotFoundError(f"Directory not found: {target}")
    if not target.is_dir():
        raise NotADirectoryError(f"Not a directory: {target}")

    if config is None:
        config = load_config()

    categories = config.get("categories", {})
    excluded_dirs = set(config.get("excluded_dirs", []))

    files: list[FileInfo] = []
    scanned_count = 0
    skipped_dirs = 0

    logger.info(f"Scanning directory: {target}")
    logger.info(f"Recursive: {recursive} | Excluded: {excluded_dirs}")

    # Get all files
    pattern = "**/*" if recursive else "*"
    for item in target.glob(pattern):
        # Skip excluded directories
        if any(excluded in item.parts for excluded in excluded_dirs):
            continue

        if not item.is_file():
            continue

        scanned_count += 1

        try:
            stat = item.stat()
            ext = item.suffix.lower()
            category = get_category(ext, categories)

            file_info = FileInfo(
                path=item,
                name=item.name,
                extension=ext,
                category=category,
                size=stat.st_size,
                size_human=format_size(stat.st_size),
                created=get_file_created_date(item),
                modified=get_file_date(item),
            )
            files.append(file_info)

        except (OSError, PermissionError) as e:
            logger.warning(f"Could not access file {item}: {e}")
            continue

        # Log progress every 100 files
        if scanned_count % 100 == 0:
            logger.debug(f"Scanned {scanned_count} files...")

    logger.info(f"Scan complete: {len(files)} files found ({scanned_count} total scanned)")
    return files


def get_scan_summary(files: list[FileInfo]) -> dict:
    """
    Generate a summary of scanned files.

    Args:
        files: List of FileInfo objects from scan_directory.

    Returns:
        Dictionary with summary statistics.
    """
    if not files:
        return {
            "total_files": 0,
            "total_size": 0,
            "total_size_human": "0 B",
            "categories": {},
            "extension_counts": {},
            "oldest_file": None,
            "newest_file": None,
        }

    total_size = sum(f.size for f in files)

    # Category breakdown
    categories: dict[str, dict] = {}
    for f in files:
        if f.category not in categories:
            categories[f.category] = {"count": 0, "size": 0}
        categories[f.category]["count"] += 1
        categories[f.category]["size"] += f.size

    # Add human-readable sizes
    for cat in categories:
        categories[cat]["size_human"] = format_size(categories[cat]["size"])

    # Extension counts
    ext_counts: dict[str, int] = {}
    for f in files:
        ext = f.extension if f.extension else "(no extension)"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1

    # Sort by count
    ext_counts = dict(sorted(ext_counts.items(), key=lambda x: x[1], reverse=True))

    # Oldest and newest
    oldest = min(files, key=lambda f: f.modified)
    newest = max(files, key=lambda f: f.modified)

    return {
        "total_files": len(files),
        "total_size": total_size,
        "total_size_human": format_size(total_size),
        "categories": categories,
        "extension_counts": ext_counts,
        "oldest_file": {"name": oldest.name, "date": oldest.modified.isoformat()},
        "newest_file": {"name": newest.name, "date": newest.modified.isoformat()},
    }


def print_scan_summary(summary: dict) -> None:
    """
    Pretty-print the scan summary to console.

    Args:
        summary: Summary dictionary from get_scan_summary.
    """
    print_banner("SCAN RESULTS")

    print(f"  [FILES] Total Files:  {summary['total_files']}")
    print(f"  [SIZE]  Total Size:   {summary['total_size_human']}")

    if summary.get("oldest_file"):
        print(f"  [DATE]  Oldest File:  {summary['oldest_file']['name']} ({summary['oldest_file']['date'][:10]})")
    if summary.get("newest_file"):
        print(f"  [DATE]  Newest File:  {summary['newest_file']['name']} ({summary['newest_file']['date'][:10]})")

    # Category breakdown table
    if summary.get("categories"):
        print(f"\n  {'-' * 50}")
        print(f"  CATEGORY BREAKDOWN")
        print(f"  {'-' * 50}")

        category_icons = {
            "Documents": "[DOC]", "Images": "[IMG]", "Code": "[CODE]",
            "Archives": "[ZIP]", "Media": "[MED]", "Data": "[DAT]", "Other": "[OTH]",
        }

        headers = ["Category", "Count", "Size"]
        rows = []
        for cat, data in sorted(summary["categories"].items(), key=lambda x: x[1]["count"], reverse=True):
            icon = category_icons.get(cat, "[OTH]")
            rows.append([f"{icon} {cat}", str(data["count"]), data["size_human"]])

        print_table(headers, rows)

    # Top extensions
    if summary.get("extension_counts"):
        print(f"\n  {'-' * 50}")
        print(f"  TOP EXTENSIONS")
        print(f"  {'-' * 50}")

        headers = ["Extension", "Count"]
        rows = [[ext, str(count)] for ext, count in list(summary["extension_counts"].items())[:10]]
        print_table(headers, rows)

    print()
