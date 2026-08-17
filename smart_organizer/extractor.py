"""
Data & Metadata Extractor for Smart File Organizer.

Extracts metadata from CSV files (row counts, column stats),
images (dimensions, EXIF data), and text files (word/line counts).
"""

import logging
from pathlib import Path
from typing import Optional

from .utils import format_size, print_banner

logger = logging.getLogger("smart_organizer.extractor")


def extract_csv_metadata(file_path: Path) -> dict:
    """
    Extract metadata and basic statistics from a CSV file.

    Args:
        file_path: Path to the CSV file.

    Returns:
        Dictionary with CSV metadata and statistics.
    """
    metadata = {
        "filename": file_path.name,
        "file_path": str(file_path),
        "type": "csv",
        "file_size": file_path.stat().st_size,
        "file_size_human": format_size(file_path.stat().st_size),
    }

    try:
        import pandas as pd

        # Try different encodings
        df = None
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            metadata["error"] = "Could not decode file with supported encodings"
            return metadata

        metadata.update({
            "row_count": len(df),
            "column_count": len(df.columns),
            "column_names": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        })

        # Numeric column statistics
        numeric_cols = df.select_dtypes(include=["number"])
        if not numeric_cols.empty:
            stats = {}
            for col in numeric_cols.columns:
                stats[col] = {
                    "mean": round(float(df[col].mean()), 2),
                    "min": round(float(df[col].min()), 2),
                    "max": round(float(df[col].max()), 2),
                    "std": round(float(df[col].std()), 2),
                }
            metadata["numeric_stats"] = stats

        # Sample rows (first 3)
        sample = df.head(3).to_dict(orient="records")
        # Convert any non-serializable types
        clean_sample = []
        for row in sample:
            clean_row = {}
            for k, v in row.items():
                try:
                    clean_row[k] = v if isinstance(v, (str, int, float, bool, type(None))) else str(v)
                except Exception:
                    clean_row[k] = str(v)
            clean_sample.append(clean_row)
        metadata["sample_rows"] = clean_sample

    except ImportError:
        metadata["error"] = "pandas not installed — install with: pip install pandas"
        logger.warning("pandas not available for CSV extraction")
    except Exception as e:
        metadata["error"] = f"Error reading CSV: {str(e)}"
        logger.error(f"CSV extraction error for {file_path}: {e}")

    return metadata


def extract_image_metadata(file_path: Path) -> dict:
    """
    Extract metadata and EXIF data from an image file.

    Args:
        file_path: Path to the image file.

    Returns:
        Dictionary with image metadata and EXIF data.
    """
    metadata = {
        "filename": file_path.name,
        "file_path": str(file_path),
        "type": "image",
        "file_size": file_path.stat().st_size,
        "file_size_human": format_size(file_path.stat().st_size),
    }

    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        with Image.open(file_path) as img:
            metadata.update({
                "format": img.format,
                "mode": img.mode,
                "width": img.size[0],
                "height": img.size[1],
                "dimensions": f"{img.size[0]}x{img.size[1]}",
            })

            # Extract EXIF data
            exif_data = {}
            try:
                raw_exif = img._getexif()
                if raw_exif:
                    for tag_id, value in raw_exif.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        # Only include common, serializable tags
                        if isinstance(tag_name, str) and isinstance(value, (str, int, float)):
                            exif_data[tag_name] = value

                    metadata["has_exif"] = True
                    metadata["exif_data"] = exif_data

                    # Extract specific useful EXIF fields
                    if "Make" in exif_data:
                        metadata["camera_make"] = exif_data["Make"]
                    if "Model" in exif_data:
                        metadata["camera_model"] = exif_data["Model"]
                    if "DateTimeOriginal" in exif_data:
                        metadata["date_taken"] = exif_data["DateTimeOriginal"]
                    elif "DateTime" in exif_data:
                        metadata["date_taken"] = exif_data["DateTime"]
                else:
                    metadata["has_exif"] = False
            except (AttributeError, Exception):
                metadata["has_exif"] = False

    except ImportError:
        metadata["error"] = "Pillow not installed — install with: pip install Pillow"
        logger.warning("Pillow not available for image extraction")
    except Exception as e:
        metadata["error"] = f"Error reading image: {str(e)}"
        logger.error(f"Image extraction error for {file_path}: {e}")

    return metadata


def extract_text_metadata(file_path: Path) -> dict:
    """
    Extract metadata from a text file.

    Args:
        file_path: Path to the text file.

    Returns:
        Dictionary with text file metadata.
    """
    metadata = {
        "filename": file_path.name,
        "file_path": str(file_path),
        "type": "text",
        "file_size": file_path.stat().st_size,
        "file_size_human": format_size(file_path.stat().st_size),
    }

    encoding_used = "utf-8"
    content = None

    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            encoding_used = encoding
            break
        except (UnicodeDecodeError, OSError):
            continue

    if content is not None:
        lines = content.splitlines()
        words = content.split()

        metadata.update({
            "encoding": encoding_used,
            "line_count": len(lines),
            "word_count": len(words),
            "char_count": len(content),
        })
    else:
        metadata["error"] = "Could not decode file"

    return metadata


def extract_metadata(file_path: Path, category: str = "") -> dict:
    """
    Route to the appropriate metadata extractor based on file type.

    Args:
        file_path: Path to the file.
        category: File category (e.g., 'Images', 'Data', 'Documents').

    Returns:
        Dictionary with extracted metadata.
    """
    file_path = Path(file_path)
    ext = file_path.suffix.lower()

    # CSV/Data files
    if ext == ".csv":
        return extract_csv_metadata(file_path)

    # Image files
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    if ext in image_extensions or category == "Images":
        return extract_image_metadata(file_path)

    # Text/Code files
    text_extensions = {".txt", ".md", ".py", ".js", ".html", ".css", ".java",
                       ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".log", ".rtf"}
    if ext in text_extensions or category in ("Documents", "Code"):
        return extract_text_metadata(file_path)

    # Default: basic metadata
    return {
        "filename": file_path.name,
        "file_path": str(file_path),
        "type": "unknown",
        "file_size": file_path.stat().st_size,
        "file_size_human": format_size(file_path.stat().st_size),
    }


def print_extraction_summary(metadata_list: list[dict]) -> None:
    """
    Pretty-print extracted metadata to console.

    Args:
        metadata_list: List of metadata dictionaries.
    """
    print_banner("METADATA EXTRACTION RESULTS")

    print(f"  [LIST] Files Analyzed: {len(metadata_list)}\n")

    for i, meta in enumerate(metadata_list, 1):
        file_type = meta.get("type", "unknown")
        print(f"  {'-' * 50}")
        print(f"  [{i}] {meta.get('filename', 'unknown')}  ({file_type.upper()})")
        print(f"  {'-' * 50}")

        if file_type == "csv":
            print(f"    Rows:     {meta.get('row_count', 'N/A')}")
            print(f"    Columns:  {meta.get('column_count', 'N/A')}")
            if meta.get("column_names"):
                cols = ", ".join(meta["column_names"][:8])
                if len(meta["column_names"]) > 8:
                    cols += f" ... (+{len(meta['column_names']) - 8} more)"
                print(f"    Names:    {cols}")
            if meta.get("numeric_stats"):
                print(f"    Stats:")
                for col, stats in meta["numeric_stats"].items():
                    print(f"      {col}: mean={stats['mean']}, "
                          f"min={stats['min']}, max={stats['max']}")

        elif file_type == "image":
            print(f"    Format:     {meta.get('format', 'N/A')}")
            print(f"    Dimensions: {meta.get('dimensions', 'N/A')}")
            print(f"    Mode:       {meta.get('mode', 'N/A')}")
            if meta.get("has_exif"):
                print(f"    EXIF:       Yes")
                if meta.get("camera_make"):
                    print(f"    Camera:     {meta.get('camera_make')} {meta.get('camera_model', '')}")
                if meta.get("date_taken"):
                    print(f"    Date Taken: {meta.get('date_taken')}")
            else:
                print(f"    EXIF:       No")

        elif file_type == "text":
            print(f"    Encoding: {meta.get('encoding', 'N/A')}")
            print(f"    Lines:    {meta.get('line_count', 'N/A')}")
            print(f"    Words:    {meta.get('word_count', 'N/A')}")
            print(f"    Chars:    {meta.get('char_count', 'N/A')}")

        print(f"    Size:     {meta.get('file_size_human', 'N/A')}")

        if meta.get("error"):
            print(f"    [WARN] Error:  {meta['error']}")

    print()
