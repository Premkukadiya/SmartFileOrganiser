"""
File Organization Engine for Smart File Organizer.

Moves or copies files into a structured folder layout by category
and date, supports configurable rename patterns, dry-run mode,
and undo/rollback of the last operation.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .utils import format_size, print_banner, print_table

logger = logging.getLogger("smart_organizer.organizer")


def build_destination_path(
    file_info,
    output_dir: str = "Organized",
    rename_pattern: str = "{date}_{original}",
    counter: int = 0,
) -> Path:
    """
    Construct the destination path for an organized file.

    Layout: output_dir/Category/Year/filename

    Args:
        file_info: FileInfo object with file metadata.
        output_dir: Root output directory.
        rename_pattern: Pattern for renaming files.
        counter: Counter for sequential naming.

    Returns:
        Destination Path object.
    """
    category = file_info.category
    modified = file_info.modified
    year = str(modified.year)
    date_str = modified.strftime("%Y-%m-%d")

    # Build new filename from pattern
    original_stem = file_info.path.stem
    original_ext = file_info.extension

    new_name = rename_pattern.replace("{date}", date_str)
    new_name = new_name.replace("{original}", original_stem)
    new_name = new_name.replace("{counter}", str(counter).zfill(4))
    new_name = f"{new_name}{original_ext}"

    dest_path = Path(output_dir) / category / year / new_name
    return dest_path


def _resolve_conflict(dest_path: Path) -> Path:
    """
    Handle filename conflicts by appending a numeric suffix.

    Args:
        dest_path: The intended destination path.

    Returns:
        A unique destination path.
    """
    if not dest_path.exists():
        return dest_path

    stem = dest_path.stem
    ext = dest_path.suffix
    parent = dest_path.parent
    counter = 1

    while True:
        new_name = f"{stem}_{counter}{ext}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def organize_files(
    file_list: list,
    output_dir: str = "Organized",
    rename_pattern: str = "{date}_{original}",
    mode: str = "copy",
    dry_run: bool = True,
) -> dict:
    """
    Organize files into a structured directory layout.

    Args:
        file_list: List of FileInfo objects to organize.
        output_dir: Root directory for organized files.
        rename_pattern: Pattern for renaming files.
        mode: 'copy' or 'move'.
        dry_run: If True, show what would happen without moving files.

    Returns:
        Results dictionary with operation details.
    """
    results = {
        "processed": 0,
        "skipped": 0,
        "errors": 0,
        "operations": [],
        "total_size": 0,
        "mode": mode,
        "dry_run": dry_run,
    }

    output_path = Path(output_dir).resolve()

    if dry_run:
        logger.info("=" * 50)
        logger.info("  DRY RUN MODE - No files will be moved or copied")
        logger.info("=" * 50)
    else:
        logger.info(f"Organizing {len(file_list)} files into: {output_path}")

    for i, file_info in enumerate(file_list, 1):
        try:
            src = file_info.path
            dest = build_destination_path(file_info, output_dir, rename_pattern, i)
            dest = dest.resolve()

            # Skip if source is inside the output directory
            try:
                src.relative_to(output_path)
                results["skipped"] += 1
                continue
            except ValueError:
                pass  # Not inside output dir — good

            # Resolve conflicts
            if not dry_run:
                dest = _resolve_conflict(dest)

            operation = {
                "source": str(src),
                "destination": str(dest),
                "action": mode,
                "category": file_info.category,
                "size": file_info.size,
            }

            if dry_run:
                logger.info(f"  [{mode.upper()}] {src.name}")
                logger.info(f"       -> {dest}")
            else:
                # Create destination directory
                dest.parent.mkdir(parents=True, exist_ok=True)

                if mode == "copy":
                    shutil.copy2(str(src), str(dest))
                elif mode == "move":
                    shutil.move(str(src), str(dest))

                logger.info(f"  [OK] {src.name} -> {dest}")

            results["operations"].append(operation)
            results["processed"] += 1
            results["total_size"] += file_info.size

        except Exception as e:
            logger.error(f"  [ERROR] Error processing {file_info.name}: {e}")
            results["errors"] += 1

    # Save manifest for undo (only in non-dry-run mode)
    if not dry_run and results["operations"]:
        manifest_path = output_path / "manifest.json"
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "operations": results["operations"],
        }
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"Manifest saved: {manifest_path}")
        except OSError as e:
            logger.error(f"Could not save manifest: {e}")

    return results


def undo_organize(manifest_path: str = "Organized/manifest.json") -> dict:
    """
    Undo the last organize operation by restoring files.

    Args:
        manifest_path: Path to the manifest.json file.

    Returns:
        Results dictionary with restore details.
    """
    results = {"restored": 0, "errors": 0, "operations": []}
    manifest_file = Path(manifest_path).resolve()

    if not manifest_file.exists():
        logger.error(f"Manifest not found: {manifest_file}")
        return results

    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Error reading manifest: {e}")
        return results

    logger.info(f"Undoing organize from: {manifest.get('timestamp', 'unknown')}")
    logger.info(f"Original mode: {manifest.get('mode', 'unknown')}")

    operations = manifest.get("operations", [])

    for op in reversed(operations):
        src = Path(op["destination"])
        dest = Path(op["source"])

        try:
            if src.exists():
                # Restore to original location
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
                results["restored"] += 1
                results["operations"].append({
                    "from": str(src),
                    "to": str(dest),
                    "status": "restored",
                })
                logger.info(f"  [RESTORED] Restored: {dest.name}")
            else:
                logger.warning(f"  [WARN] File not found: {src}")
                results["errors"] += 1
        except Exception as e:
            logger.error(f"  [ERROR] Failed to restore {src.name}: {e}")
            results["errors"] += 1

    # Clean up empty directories in the organized folder
    organized_dir = manifest_file.parent
    _cleanup_empty_dirs(organized_dir)

    # Remove manifest after undo
    try:
        manifest_file.unlink()
        logger.info("Manifest file removed.")
    except OSError:
        pass

    return results


def _cleanup_empty_dirs(directory: Path) -> None:
    """Remove empty subdirectories recursively."""
    if not directory.is_dir():
        return
    for child in directory.iterdir():
        if child.is_dir():
            _cleanup_empty_dirs(child)
            try:
                child.rmdir()  # Only removes if empty
            except OSError:
                pass


def print_organize_summary(results: dict, dry_run: bool = True) -> None:
    """
    Pretty-print organization results.

    Args:
        results: Results dictionary from organize_files.
        dry_run: Whether this was a dry run.
    """
    print_banner("ORGANIZATION RESULTS")

    if dry_run:
        print("  [WARN] DRY RUN - No files were actually moved or copied")
        print()

    print(f"  [FILES] Files Processed: {results['processed']}")
    print(f"  [SKIP]  Files Skipped:   {results['skipped']}")
    print(f"  [ERROR] Errors:          {results['errors']}")
    print(f"  [SIZE]  Total Size:      {format_size(results.get('total_size', 0))}")
    print(f"  [MODE]  Mode:            {results.get('mode', 'copy').upper()}")

    # Show category breakdown
    if results.get("operations"):
        category_counts: dict[str, int] = {}
        for op in results["operations"]:
            cat = op.get("category", "Other")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        print(f"\n  {'-' * 40}")
        headers = ["Category", "Files"]
        rows = [[cat, str(count)] for cat, count in
                sorted(category_counts.items(), key=lambda x: x[1], reverse=True)]
        print_table(headers, rows)

    if dry_run:
        print("\n  [TIP] Run with --execute to apply these changes.")

    print()
