"""Tests for the scanner module."""

import sys
import os
from pathlib import Path
from datetime import datetime

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from smart_organizer.scanner import scan_directory, get_scan_summary, FileInfo
from smart_organizer.config import load_config


@pytest.fixture
def sample_directory(tmp_path):
    """Create a sample directory with various file types."""
    # Documents
    (tmp_path / "readme.txt").write_text("Hello World")
    (tmp_path / "report.pdf").write_bytes(b"%PDF-1.4 fake pdf content here")

    # Code
    (tmp_path / "script.py").write_text("print('hello')\n")
    (tmp_path / "style.css").write_text("body { color: red; }\n")

    # Data
    (tmp_path / "data.csv").write_text("name,age\nAlice,30\nBob,25\n")
    (tmp_path / "config.json").write_text('{"key": "value"}')

    # Images
    (tmp_path / "photo.jpg").write_bytes(b"\xff\xd8\xff fake jpg")
    (tmp_path / "icon.png").write_bytes(b"\x89PNG fake png")

    # Subdirectory
    subdir = tmp_path / "subfolder"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("nested file")

    # Excluded directory
    excluded = tmp_path / "__pycache__"
    excluded.mkdir()
    (excluded / "cached.pyc").write_bytes(b"fake bytecode")

    return tmp_path


@pytest.fixture
def config():
    """Load default config."""
    return load_config()


class TestScanDirectory:
    """Tests for scan_directory function."""

    def test_scan_finds_files(self, sample_directory, config):
        """Test that scanning finds all files."""
        files = scan_directory(sample_directory, config)
        # Should find files but NOT the __pycache__ contents
        filenames = [f.name for f in files]
        assert "readme.txt" in filenames
        assert "script.py" in filenames
        assert "data.csv" in filenames

    def test_scan_excludes_pycache(self, sample_directory, config):
        """Test that excluded directories are skipped."""
        files = scan_directory(sample_directory, config)
        filenames = [f.name for f in files]
        assert "cached.pyc" not in filenames

    def test_scan_recursive(self, sample_directory, config):
        """Test recursive scanning includes subdirectories."""
        files = scan_directory(sample_directory, config, recursive=True)
        filenames = [f.name for f in files]
        assert "nested.txt" in filenames

    def test_scan_non_recursive(self, sample_directory, config):
        """Test non-recursive scanning skips subdirectories."""
        files = scan_directory(sample_directory, config, recursive=False)
        filenames = [f.name for f in files]
        assert "nested.txt" not in filenames

    def test_scan_empty_directory(self, tmp_path, config):
        """Test scanning an empty directory returns empty list."""
        files = scan_directory(tmp_path, config)
        assert files == []

    def test_scan_nonexistent_directory(self, config):
        """Test scanning a non-existent directory raises error."""
        with pytest.raises(FileNotFoundError):
            scan_directory("/nonexistent/path", config)

    def test_file_info_fields(self, sample_directory, config):
        """Test that FileInfo objects have correct fields."""
        files = scan_directory(sample_directory, config)
        txt_files = [f for f in files if f.name == "readme.txt"]
        assert len(txt_files) == 1

        f = txt_files[0]
        assert f.extension == ".txt"
        assert f.category == "Documents"
        assert f.size > 0
        assert isinstance(f.created, datetime)
        assert isinstance(f.modified, datetime)


class TestFileClassification:
    """Tests for file classification by category."""

    def test_document_classification(self, sample_directory, config):
        """Test documents are classified correctly."""
        files = scan_directory(sample_directory, config)
        txt = [f for f in files if f.name == "readme.txt"][0]
        assert txt.category == "Documents"

    def test_code_classification(self, sample_directory, config):
        """Test code files are classified correctly."""
        files = scan_directory(sample_directory, config)
        py = [f for f in files if f.name == "script.py"][0]
        assert py.category == "Code"

    def test_data_classification(self, sample_directory, config):
        """Test data files are classified correctly."""
        files = scan_directory(sample_directory, config)
        csv_file = [f for f in files if f.name == "data.csv"][0]
        assert csv_file.category == "Data"

    def test_image_classification(self, sample_directory, config):
        """Test image files are classified correctly."""
        files = scan_directory(sample_directory, config)
        jpg = [f for f in files if f.name == "photo.jpg"][0]
        assert jpg.category == "Images"


class TestScanSummary:
    """Tests for get_scan_summary function."""

    def test_summary_total_files(self, sample_directory, config):
        """Test summary has correct total file count."""
        files = scan_directory(sample_directory, config)
        summary = get_scan_summary(files)
        assert summary["total_files"] == len(files)

    def test_summary_total_size(self, sample_directory, config):
        """Test summary has correct total size."""
        files = scan_directory(sample_directory, config)
        summary = get_scan_summary(files)
        assert summary["total_size"] == sum(f.size for f in files)
        assert summary["total_size_human"] != ""

    def test_summary_categories(self, sample_directory, config):
        """Test summary has category breakdown."""
        files = scan_directory(sample_directory, config)
        summary = get_scan_summary(files)
        assert "categories" in summary
        assert "Documents" in summary["categories"]

    def test_summary_empty_list(self):
        """Test summary handles empty file list."""
        summary = get_scan_summary([])
        assert summary["total_files"] == 0
        assert summary["total_size"] == 0

    def test_summary_has_extension_counts(self, sample_directory, config):
        """Test summary includes extension counts."""
        files = scan_directory(sample_directory, config)
        summary = get_scan_summary(files)
        assert "extension_counts" in summary
        assert ".txt" in summary["extension_counts"]

    def test_file_info_to_dict(self, sample_directory, config):
        """Test FileInfo.to_dict serialization."""
        files = scan_directory(sample_directory, config)
        d = files[0].to_dict()
        assert "path" in d
        assert "name" in d
        assert "category" in d
        assert isinstance(d["path"], str)
