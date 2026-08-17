"""
Configuration loader for Smart File Organizer.

Loads settings from YAML config files, provides default category
mappings, and utility functions for file classification.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("smart_organizer.config")

# Default extension-to-category mappings
DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pptx", ".ppt"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".ico"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".h",
             ".go", ".rs", ".rb", ".php", ".sh", ".bat"],
    "Archives": [".zip", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz"],
    "Media": [".mp3", ".mp4", ".avi", ".mkv", ".wav", ".flac", ".mov", ".wmv",
              ".ogg", ".webm"],
    "Data": [".csv", ".json", ".xml", ".xlsx", ".xls", ".sql", ".db", ".sqlite"],
}

DEFAULT_CONFIG: dict = {
    "categories": DEFAULT_CATEGORIES,
    "output_directory": "Organized",
    "rename_pattern": "{date}_{original}",
    "excluded_dirs": [".git", "__pycache__", "node_modules", ".venv", "venv",
                      "Organized", ".idea", ".vscode"],
    "hash_algorithm": "sha256",
    "log_file": "organizer.log",
}


def load_config(config_path: Optional[str | Path] = None) -> dict:
    """
    Load configuration from a YAML file and merge with defaults.

    Args:
        config_path: Path to the YAML config file. If None, uses defaults.

    Returns:
        Configuration dictionary with all settings.
    """
    config = DEFAULT_CONFIG.copy()

    if config_path is None:
        # Try to find config.yaml in common locations
        search_paths = [
            Path("config.yaml"),
            Path("config.yml"),
            Path.home() / ".smart_organizer" / "config.yaml",
        ]
        for p in search_paths:
            if p.exists():
                config_path = p
                break

    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            try:
                import yaml
                with open(config_file, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)

                if user_config and isinstance(user_config, dict):
                    # Merge categories (user config extends defaults)
                    if "categories" in user_config:
                        merged_categories = DEFAULT_CATEGORIES.copy()
                        merged_categories.update(user_config["categories"])
                        config["categories"] = merged_categories
                        user_config.pop("categories")

                    config.update(user_config)
                    logger.info(f"Loaded config from: {config_file}")
            except ImportError:
                logger.warning("PyYAML not installed. Using default configuration.")
            except Exception as e:
                logger.warning(f"Error loading config '{config_file}': {e}. Using defaults.")
        else:
            logger.debug(f"Config file not found: {config_file}. Using defaults.")

    return config


def get_category(extension: str, categories: Optional[dict[str, list[str]]] = None) -> str:
    """
    Determine the category of a file based on its extension.

    Args:
        extension: File extension (e.g., '.pdf').
        categories: Category mapping dict. Uses defaults if None.

    Returns:
        Category name string (e.g., 'Documents', 'Images', 'Other').
    """
    if categories is None:
        categories = DEFAULT_CATEGORIES

    ext_lower = extension.lower()

    for category, extensions in categories.items():
        if ext_lower in extensions:
            return category

    return "Other"
