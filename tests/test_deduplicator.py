"""Tests for the deduplicator module."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from smart_organizer.deduplicator import hash_file, find_duplicates, get_duplicate_summary, remove_duplicates


@pytest.fixture
def duplicate_files(tmp_path):
    """Create files with duplicate content."""
    content = b"This is duplicate content for testing purposes."

    file1 = tmp_path / "original.txt"
    file1.write_bytes(content)

    file2 = tmp_path / "copy1.txt"
    file2.write_bytes(content)

    file3 = tmp_path / "copy2.txt"
    file3.write_bytes(content)

    return [file1, file2, file3]


@pytest.fixture
def unique_files(tmp_path):
    """Create files with unique content."""
    file1 = tmp_path / "unique1.txt"
    file1.write_text("Unique content one")

    file2 = tmp_path / "unique2.txt"
    file2.write_text("Unique content two")

    file3 = tmp_path / "unique3.txt"
    file3.write_text("Unique content three")

    return [file1, file2, file3]


class TestHashFile:
    """Tests for hash_file function."""

    def test_consistent_hash(self, tmp_path):
        """Test that hashing the same file gives the same result."""
        f = tmp_path / "test.txt"
        f.write_text("Hello World")

        hash1 = hash_file(f)
        hash2 = hash_file(f)
        assert hash1 == hash2

    def test_different_content_different_hash(self, tmp_path):
        """Test that different content produces different hashes."""
        f1 = tmp_path / "file1.txt"
        f1.write_text("Content A")

        f2 = tmp_path / "file2.txt"
        f2.write_text("Content B")

        assert hash_file(f1) != hash_file(f2)

    def test_same_content_same_hash(self, duplicate_files):
        """Test that same content produces same hash."""
        hashes = [hash_file(f) for f in duplicate_files]
        assert all(h == hashes[0] for h in hashes)

    def test_md5_algorithm(self, tmp_path):
        """Test hashing with MD5 algorithm."""
        f = tmp_path / "test.txt"
        f.write_text("Test content")

        sha_hash = hash_file(f, algorithm="sha256")
        md5_hash = hash_file(f, algorithm="md5")

        assert sha_hash != md5_hash  # Different algorithms
        assert len(md5_hash) == 32  # MD5 hex length
        assert len(sha_hash) == 64  # SHA256 hex length

    def test_nonexistent_file(self, tmp_path):
        """Test hashing a nonexistent file returns empty string."""
        result = hash_file(tmp_path / "nonexistent.txt")
        assert result == ""


class TestFindDuplicates:
    """Tests for find_duplicates function."""

    def test_finds_duplicates(self, duplicate_files):
        """Test that duplicates are correctly identified."""
        duplicates = find_duplicates(duplicate_files)
        assert len(duplicates) == 1  # One group of duplicates
        # The group should contain all 3 files
        group = list(duplicates.values())[0]
        assert len(group) == 3

    def test_no_duplicates_for_unique_files(self, unique_files):
        """Test that unique files produce no duplicates."""
        duplicates = find_duplicates(unique_files)
        assert len(duplicates) == 0

    def test_empty_list(self):
        """Test with empty file list."""
        duplicates = find_duplicates([])
        assert len(duplicates) == 0

    def test_mixed_files(self, tmp_path):
        """Test with mix of unique and duplicate files."""
        # Create duplicates
        dup_content = b"Duplicate content"
        f1 = tmp_path / "dup1.txt"
        f1.write_bytes(dup_content)
        f2 = tmp_path / "dup2.txt"
        f2.write_bytes(dup_content)

        # Create unique
        f3 = tmp_path / "unique.txt"
        f3.write_text("Unique content here")

        duplicates = find_duplicates([f1, f2, f3])
        assert len(duplicates) == 1


class TestDuplicateSummary:
    """Tests for get_duplicate_summary function."""

    def test_summary_stats(self, duplicate_files):
        """Test summary returns correct statistics."""
        duplicates = find_duplicates(duplicate_files)
        summary = get_duplicate_summary(duplicates)

        assert summary["total_duplicate_groups"] == 1
        assert summary["total_duplicate_files"] == 2  # 3 files - 1 original = 2 dupes
        assert summary["total_space_recoverable"] > 0
        assert len(summary["details"]) == 1

    def test_empty_summary(self):
        """Test summary with no duplicates."""
        summary = get_duplicate_summary({})
        assert summary["total_duplicate_groups"] == 0
        assert summary["total_duplicate_files"] == 0


class TestRemoveDuplicates:
    """Tests for remove_duplicates function."""

    def test_dry_run_no_delete(self, duplicate_files):
        """Test dry run doesn't delete files."""
        duplicates = find_duplicates(duplicate_files)
        deleted = remove_duplicates(duplicates, dry_run=True)

        assert len(deleted) == 2  # Would delete 2 duplicates
        # But all files should still exist
        for f in duplicate_files:
            assert f.exists()

    def test_execute_deletes(self, duplicate_files):
        """Test execute mode actually deletes duplicates."""
        duplicates = find_duplicates(duplicate_files)
        deleted = remove_duplicates(duplicates, dry_run=False, keep="oldest")

        assert len(deleted) == 2
        # Only original should remain
        remaining = [f for f in duplicate_files if f.exists()]
        assert len(remaining) == 1
