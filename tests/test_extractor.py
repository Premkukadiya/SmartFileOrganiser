"""Tests for the extractor module."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from smart_organizer.extractor import (
    extract_csv_metadata,
    extract_text_metadata,
    extract_image_metadata,
    extract_metadata,
)


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file."""
    csv_content = "Name,Age,Salary,City\nAlice,30,50000,Mumbai\nBob,25,45000,Delhi\nCharlie,35,60000,Pune\n"
    f = tmp_path / "test.csv"
    f.write_text(csv_content)
    return f


@pytest.fixture
def sample_text(tmp_path):
    """Create a sample text file."""
    text = "Hello World\nThis is a test file.\nIt has multiple lines.\nFor testing purposes.\n"
    f = tmp_path / "test.txt"
    f.write_text(text)
    return f


@pytest.fixture
def sample_image(tmp_path):
    """Create a small test image using Pillow."""
    try:
        from PIL import Image
        img = Image.new("RGB", (100, 50), color="red")
        f = tmp_path / "test.png"
        img.save(str(f))
        return f
    except ImportError:
        pytest.skip("Pillow not installed")


class TestCSVExtractor:
    """Tests for CSV metadata extraction."""

    def test_csv_row_count(self, sample_csv):
        """Test CSV row count extraction."""
        meta = extract_csv_metadata(sample_csv)
        assert meta["row_count"] == 3

    def test_csv_column_names(self, sample_csv):
        """Test CSV column names extraction."""
        meta = extract_csv_metadata(sample_csv)
        assert meta["column_names"] == ["Name", "Age", "Salary", "City"]
        assert meta["column_count"] == 4

    def test_csv_numeric_stats(self, sample_csv):
        """Test CSV numeric statistics."""
        meta = extract_csv_metadata(sample_csv)
        assert "numeric_stats" in meta
        assert "Age" in meta["numeric_stats"]
        assert meta["numeric_stats"]["Age"]["mean"] == 30.0

    def test_csv_sample_rows(self, sample_csv):
        """Test CSV sample rows extraction."""
        meta = extract_csv_metadata(sample_csv)
        assert "sample_rows" in meta
        assert len(meta["sample_rows"]) == 3

    def test_csv_file_type(self, sample_csv):
        """Test metadata type field."""
        meta = extract_csv_metadata(sample_csv)
        assert meta["type"] == "csv"
        assert meta["filename"] == "test.csv"


class TestTextExtractor:
    """Tests for text file metadata extraction."""

    def test_text_line_count(self, sample_text):
        """Test text file line count."""
        meta = extract_text_metadata(sample_text)
        assert meta["line_count"] == 4

    def test_text_word_count(self, sample_text):
        """Test text file word count."""
        meta = extract_text_metadata(sample_text)
        assert meta["word_count"] > 0

    def test_text_char_count(self, sample_text):
        """Test text file character count."""
        meta = extract_text_metadata(sample_text)
        assert meta["char_count"] > 0

    def test_text_encoding(self, sample_text):
        """Test encoding detection."""
        meta = extract_text_metadata(sample_text)
        assert meta["encoding"] == "utf-8"

    def test_text_file_type(self, sample_text):
        """Test metadata type field."""
        meta = extract_text_metadata(sample_text)
        assert meta["type"] == "text"


class TestImageExtractor:
    """Tests for image metadata extraction."""

    def test_image_dimensions(self, sample_image):
        """Test image dimensions extraction."""
        meta = extract_image_metadata(sample_image)
        assert meta["width"] == 100
        assert meta["height"] == 50
        assert meta["dimensions"] == "100x50"

    def test_image_format(self, sample_image):
        """Test image format detection."""
        meta = extract_image_metadata(sample_image)
        assert meta["format"] == "PNG"

    def test_image_mode(self, sample_image):
        """Test image mode detection."""
        meta = extract_image_metadata(sample_image)
        assert meta["mode"] == "RGB"

    def test_image_file_type(self, sample_image):
        """Test metadata type field."""
        meta = extract_image_metadata(sample_image)
        assert meta["type"] == "image"


class TestExtractMetadata:
    """Tests for the extract_metadata routing function."""

    def test_routes_csv(self, sample_csv):
        """Test routing to CSV extractor."""
        meta = extract_metadata(sample_csv, "Data")
        assert meta["type"] == "csv"

    def test_routes_text(self, sample_text):
        """Test routing to text extractor."""
        meta = extract_metadata(sample_text, "Documents")
        assert meta["type"] == "text"

    def test_routes_image(self, sample_image):
        """Test routing to image extractor."""
        meta = extract_metadata(sample_image, "Images")
        assert meta["type"] == "image"

    def test_corrupt_file(self, tmp_path):
        """Test error handling for corrupt files."""
        corrupt = tmp_path / "corrupt.csv"
        corrupt.write_bytes(b"\x00\x01\x02\x03\x04\x05")
        meta = extract_metadata(corrupt, "Data")
        # Should not raise, may have error field
        assert "filename" in meta
