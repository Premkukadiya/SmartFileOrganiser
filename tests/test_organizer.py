"""Tests for the organizer module."""

import sys
import json
from pathlib import Path
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from smart_organizer.organizer import build_destination_path, organize_files, undo_organize
from smart_organizer.scanner import scan_directory, FileInfo
from smart_organizer.config import load_config


@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for organization tests."""
    (tmp_path / "report.txt").write_text("Sample report content")
    (tmp_path / "photo.jpg").write_bytes(b"\xff\xd8\xff fake jpg data")
    (tmp_path / "script.py").write_text("print('hello')")
    (tmp_path / "data.csv").write_text("col1,col2\n1,2\n3,4")
    return tmp_path


@pytest.fixture
def config():
    """Load default config."""
    return load_config()


class TestBuildDestinationPath:
    """Tests for build_destination_path function."""

    def test_basic_destination(self):
        """Test basic destination path construction."""
        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            category="Documents",
            size=100,
            size_human="100 B",
            created=datetime(2026, 7, 15),
            modified=datetime(2026, 7, 15),
        )
        dest = build_destination_path(file_info, "Organized", "{date}_{original}")
        assert "Documents" in str(dest)
        assert "2026" in str(dest)
        assert "2026-07-15_test.txt" in str(dest)

    def test_original_only_pattern(self):
        """Test destination with original-name-only pattern."""
        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            category="Documents",
            size=100,
            size_human="100 B",
            created=datetime(2026, 1, 1),
            modified=datetime(2026, 1, 1),
        )
        dest = build_destination_path(file_info, "Output", "{original}")
        assert dest.name == "test.txt"

    def test_category_in_path(self):
        """Test that category is included in destination path."""
        file_info = FileInfo(
            path=Path("img.png"),
            name="img.png",
            extension=".png",
            category="Images",
            size=200,
            size_human="200 B",
            created=datetime(2026, 6, 1),
            modified=datetime(2026, 6, 1),
        )
        dest = build_destination_path(file_info, "Organized", "{original}")
        assert "Images" in str(dest)


class TestOrganizeFiles:
    """Tests for organize_files function."""

    def test_dry_run_no_changes(self, sample_files, config):
        """Test dry run doesn't create or move files."""
        files = scan_directory(sample_files, config)
        output_dir = str(sample_files / "Organized")

        results = organize_files(files, output_dir, dry_run=True)

        assert results["processed"] > 0
        assert results["errors"] == 0
        # Output directory should NOT be created in dry run
        # (since no actual files are moved)
        assert not Path(output_dir).exists() or not any(Path(output_dir).iterdir())

    def test_execute_creates_structure(self, sample_files, config):
        """Test execute mode creates directory structure and copies files."""
        files = scan_directory(sample_files, config)
        output_dir = str(sample_files / "TestOrganized")

        results = organize_files(files, output_dir, mode="copy", dry_run=False)

        assert results["processed"] > 0
        assert Path(output_dir).exists()

        # Check that files were actually copied
        organized_files = list(Path(output_dir).rglob("*"))
        file_count = sum(1 for f in organized_files if f.is_file() and f.name != "manifest.json")
        assert file_count > 0

    def test_manifest_created(self, sample_files, config):
        """Test that manifest.json is created after organize."""
        files = scan_directory(sample_files, config)
        output_dir = str(sample_files / "OrgManifest")

        organize_files(files, output_dir, mode="copy", dry_run=False)

        manifest = Path(output_dir) / "manifest.json"
        assert manifest.exists()

        with open(manifest) as f:
            data = json.load(f)
        assert "operations" in data
        assert "timestamp" in data

    def test_results_structure(self, sample_files, config):
        """Test that results dict has correct keys."""
        files = scan_directory(sample_files, config)
        results = organize_files(files, str(sample_files / "Org"), dry_run=True)

        assert "processed" in results
        assert "skipped" in results
        assert "errors" in results
        assert "operations" in results
        assert "mode" in results


class TestUndoOrganize:
    """Tests for undo_organize function."""

    def test_undo_restores_files(self, sample_files, config):
        """Test that undo restores files to original location."""
        files = scan_directory(sample_files, config)
        output_dir = str(sample_files / "UndoTest")

        # Organize with move mode
        organize_files(files, output_dir, mode="move", dry_run=False)

        # Verify files were moved (originals gone)
        assert not (sample_files / "report.txt").exists()

        # Undo
        manifest_path = str(Path(output_dir) / "manifest.json")
        results = undo_organize(manifest_path)

        assert results["restored"] > 0
        # Files should be back
        assert (sample_files / "report.txt").exists()

    def test_undo_missing_manifest(self, tmp_path):
        """Test undo with missing manifest returns empty results."""
        results = undo_organize(str(tmp_path / "nonexistent.json"))
        assert results["restored"] == 0
