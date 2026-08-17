"""
Shared utility functions for Smart File Organizer.

Provides logging setup, file size formatting, date helpers,
and path validation utilities used across all modules.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColorFormatter(logging.Formatter):
    """Custom logging formatter with colored console output."""

    COLORS = {
        logging.DEBUG: "\033[36m",      # Cyan
        logging.INFO: "\033[32m",       # Green
        logging.WARNING: "\033[33m",    # Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[41m",   # Red background
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{self.BOLD}{record.levelname}{self.RESET}"
        record.msg = f"{color}{record.msg}{self.RESET}"
        return super().format(record)


def setup_logging(log_file: str = "organizer.log", verbose: bool = False) -> logging.Logger:
    """
    Configure logging to both console and file.

    Args:
        log_file: Path to the log file.
        verbose: If True, set console level to DEBUG.

    Returns:
        Configured root logger.
    """
    logger = logging.getLogger("smart_organizer")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_format = ColorFormatter("%(levelname)s  %(message)s")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (plain text)
    try:
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        logger.warning(f"Could not create log file '{log_file}': {e}")

    return logger


def format_size(size_bytes: int) -> str:
    """
    Convert bytes to human-readable format.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted string like '1.5 MB'.
    """
    if size_bytes < 0:
        return "0 B"

    units = [("TB", 1024**4), ("GB", 1024**3), ("MB", 1024**2), ("KB", 1024), ("B", 1)]
    for unit, threshold in units:
        if size_bytes >= threshold:
            value = size_bytes / threshold
            if value == int(value):
                return f"{int(value)} {unit}"
            return f"{value:.2f} {unit}"
    return "0 B"


def get_file_date(path: Path) -> datetime:
    """
    Get the modification date of a file.

    Args:
        path: Path to the file.

    Returns:
        datetime of the file's last modification.
    """
    try:
        stat = path.stat()
        return datetime.fromtimestamp(stat.st_mtime)
    except (OSError, ValueError):
        return datetime.now()


def get_file_created_date(path: Path) -> datetime:
    """
    Get the creation date of a file (Windows: birth time, Unix: ctime).

    Args:
        path: Path to the file.

    Returns:
        datetime of the file's creation.
    """
    try:
        stat = path.stat()
        # On Windows, st_ctime is the creation time
        if os.name == "nt":
            return datetime.fromtimestamp(stat.st_ctime)
        # On Unix, use st_birthtime if available, else st_ctime
        birth = getattr(stat, "st_birthtime", None)
        if birth:
            return datetime.fromtimestamp(birth)
        return datetime.fromtimestamp(stat.st_ctime)
    except (OSError, ValueError):
        return datetime.now()


def safe_path(path: str | Path) -> Path:
    """
    Resolve and validate a path.

    Args:
        path: String or Path to validate.

    Returns:
        Resolved Path object.

    Raises:
        FileNotFoundError: If the path does not exist.
    """
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Path does not exist: {resolved}")
    return resolved


def print_banner(text: str, char: str = "=", width: int = 60) -> None:
    """Print a styled banner to console."""
    border = char * width
    padding = (width - len(text) - 2) // 2
    print(f"\n{border}")
    print(f"{char}{' ' * padding}{text}{' ' * (width - padding - len(text) - 2)}{char}")
    print(f"{border}\n")


def print_table(headers: list[str], rows: list[list[str]], col_widths: Optional[list[int]] = None) -> None:
    """
    Print a formatted table to console.

    Args:
        headers: List of column header strings.
        rows: List of rows, each a list of cell strings.
        col_widths: Optional list of column widths.
    """
    if not col_widths:
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(min(max_width + 2, 50))

    # Header
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * w for w in col_widths)

    print(f"  {header_line}")
    print(f"  {separator}")

    # Rows
    for row in rows:
        row_line = " | ".join(str(row[i]).ljust(col_widths[i]) if i < len(row) else " " * col_widths[i]
                              for i in range(len(headers)))
        print(f"  {row_line}")
