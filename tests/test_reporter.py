"""Tests for the reporter module."""

import sys
import json
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from smart_organizer.reporter import (
    generate_json_report,
    generate_csv_report,
    generate_html_report,
    generate_report,
)


@pytest.fixture
def scan_summary():
    """Sample scan summary data."""
    return {
        "total_files": 15,
        "total_size": 1048576,
        "total_size_human": "1 MB",
        "categories": {
            "Documents": {"count": 5, "size": 524288, "size_human": "512 KB"},
            "Images": {"count": 4, "size": 262144, "size_human": "256 KB"},
            "Code": {"count": 3, "size": 131072, "size_human": "128 KB"},
            "Data": {"count": 3, "size": 131072, "size_human": "128 KB"},
        },
        "extension_counts": {".txt": 3, ".py": 3, ".jpg": 2, ".csv": 2, ".png": 2, ".pdf": 2, ".json": 1},
        "oldest_file": {"name": "old.txt", "date": "2024-01-01T00:00:00"},
        "newest_file": {"name": "new.txt", "date": "2026-07-31T00:00:00"},
    }


@pytest.fixture
def duplicate_summary():
    """Sample duplicate summary data."""
    return {
        "total_duplicate_groups": 2,
        "total_duplicate_files": 3,
        "total_space_recoverable": 65536,
        "total_space_recoverable_human": "64 KB",
        "details": [
            {
                "hash": "abc123...",
                "file_size": 32768,
                "file_size_human": "32 KB",
                "total_copies": 2,
                "duplicate_count": 1,
                "space_recoverable": "32 KB",
                "files": ["file1.txt", "file1_copy.txt"],
            },
        ],
    }


class TestJSONReport:
    """Tests for JSON report generation."""

    def test_creates_json_file(self, tmp_path, scan_summary):
        """Test JSON report file is created."""
        output = str(tmp_path / "test_report.json")
        result = generate_json_report(scan_summary, output_path=output)
        assert Path(result).exists()

    def test_valid_json(self, tmp_path, scan_summary):
        """Test generated file is valid JSON."""
        output = str(tmp_path / "test.json")
        generate_json_report(scan_summary, output_path=output)

        with open(output) as f:
            data = json.load(f)

        assert "report_metadata" in data
        assert "scan_summary" in data

    def test_includes_scan_data(self, tmp_path, scan_summary):
        """Test report includes scan summary data."""
        output = str(tmp_path / "test.json")
        generate_json_report(scan_summary, output_path=output)

        with open(output) as f:
            data = json.load(f)

        assert data["scan_summary"]["total_files"] == 15

    def test_includes_duplicates(self, tmp_path, scan_summary, duplicate_summary):
        """Test report includes duplicate data when provided."""
        output = str(tmp_path / "test.json")
        generate_json_report(scan_summary, duplicate_summary, output_path=output)

        with open(output) as f:
            data = json.load(f)

        assert "duplicate_summary" in data


class TestCSVReport:
    """Tests for CSV report generation."""

    def test_creates_csv_file(self, tmp_path, scan_summary):
        """Test CSV report file is created."""
        output = str(tmp_path / "test_report.csv")
        result = generate_csv_report(scan_summary, output_path=output)
        assert Path(result).exists()

    def test_csv_has_content(self, tmp_path, scan_summary):
        """Test CSV file has content."""
        output = str(tmp_path / "test.csv")
        generate_csv_report(scan_summary, output_path=output)

        content = Path(output).read_text()
        assert "SCAN SUMMARY" in content
        assert "Total Files" in content


class TestHTMLReport:
    """Tests for HTML report generation."""

    def test_creates_html_file(self, tmp_path, scan_summary):
        """Test HTML report file is created."""
        output = str(tmp_path / "test_report.html")
        result = generate_html_report(scan_summary, output_path=output)
        assert Path(result).exists()

    def test_valid_html(self, tmp_path, scan_summary):
        """Test generated file is valid HTML."""
        output = str(tmp_path / "test.html")
        generate_html_report(scan_summary, output_path=output)

        content = Path(output).read_text(encoding='utf-8')
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "Smart File Organizer" in content

    def test_includes_categories(self, tmp_path, scan_summary):
        """Test HTML includes category data."""
        output = str(tmp_path / "test.html")
        generate_html_report(scan_summary, output_path=output)

        content = Path(output).read_text(encoding='utf-8')
        assert "Documents" in content
        assert "Images" in content

    def test_includes_duplicate_section(self, tmp_path, scan_summary, duplicate_summary):
        """Test HTML includes duplicate section when provided."""
        output = str(tmp_path / "test.html")
        generate_html_report(scan_summary, duplicate_summary, output_path=output)

        content = Path(output).read_text(encoding='utf-8')
        assert "Duplicate" in content


class TestGenerateReport:
    """Tests for the generate_report routing function."""

    def test_routes_json(self, tmp_path, scan_summary):
        """Test routing to JSON generator."""
        output = str(tmp_path / "routed.json")
        result = generate_report(scan_summary, format="json", output_path=output)
        assert result.endswith(".json")
        assert Path(result).exists()

    def test_routes_csv(self, tmp_path, scan_summary):
        """Test routing to CSV generator."""
        output = str(tmp_path / "routed.csv")
        result = generate_report(scan_summary, format="csv", output_path=output)
        assert result.endswith(".csv")

    def test_routes_html(self, tmp_path, scan_summary):
        """Test routing to HTML generator."""
        output = str(tmp_path / "routed.html")
        result = generate_report(scan_summary, format="html", output_path=output)
        assert result.endswith(".html")

    def test_invalid_format(self, scan_summary):
        """Test invalid format raises error."""
        with pytest.raises(ValueError):
            generate_report(scan_summary, format="pdf")
