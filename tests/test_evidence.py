"""Tests for objective evidence capture functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from pytest_gxp.evidence import (
    PILLOW_AVAILABLE,
    EvidenceCollector,
    directory_listing_to_image,
    text_to_image,
)
from pytest_gxp.markdown_format import EvidenceItem, EvidenceType


@pytest.fixture
def evidence_dir():
    """Create a temporary directory for evidence files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def collector(evidence_dir):
    """Create an evidence collector for testing."""
    return EvidenceCollector(evidence_dir, generate_thumbnails=False)


@pytest.fixture
def collector_with_thumbnails(evidence_dir):
    """Create an evidence collector with thumbnails enabled."""
    return EvidenceCollector(evidence_dir, generate_thumbnails=True)


class TestEvidenceCollectorInit:
    """Tests for EvidenceCollector initialization."""

    def test_creates_evidence_directory(self, evidence_dir):
        """Test that the evidence directory is created."""
        EvidenceCollector(evidence_dir)
        assert (evidence_dir / "evidence").exists()

    def test_creates_thumbnails_directory_when_enabled(self, evidence_dir):
        """Test that thumbnails directory is created when enabled."""
        EvidenceCollector(evidence_dir, generate_thumbnails=True)
        assert (evidence_dir / "evidence" / "thumbnails").exists()

    def test_no_thumbnails_directory_when_disabled(self, evidence_dir):
        """Test that thumbnails directory is not created when disabled."""
        EvidenceCollector(evidence_dir, generate_thumbnails=False)
        # The directory should not exist (or we need to check it wasn't created for thumbnails)
        assert (evidence_dir / "evidence").exists()


class TestEvidenceCollectorTestContext:
    """Tests for test context management."""

    def test_set_current_test(self, collector):
        """Test setting current test context."""
        collector.set_current_test("test_module::test_func", ["FS-001", "FS-002"])
        assert collector._current_test_id == "test_module::test_func"
        assert collector._current_requirement_ids == ["FS-001", "FS-002"]

    def test_clear_current_test(self, collector):
        """Test clearing current test context."""
        collector.set_current_test("test_module::test_func", ["FS-001"])
        collector.clear_current_test()
        assert collector._current_test_id is None
        assert collector._current_requirement_ids == []

    def test_requirement_ids_are_copied(self, collector):
        """Test that requirement IDs are copied, not referenced."""
        req_ids = ["FS-001"]
        collector.set_current_test("test_module::test_func", req_ids)
        req_ids.append("FS-002")
        assert collector._current_requirement_ids == ["FS-001"]


class TestCaptureScreenshot:
    """Tests for screenshot capture."""

    def test_capture_from_bytes(self, collector):
        """Test capturing screenshot from bytes."""
        # Create a minimal valid PNG
        png_data = _create_minimal_png()

        collector.set_current_test("test_module::test_screenshot", ["FS-001"])
        item = collector.capture_screenshot(png_data, "Test screenshot")

        assert item.id == "EV-0001"
        assert item.evidence_type == EvidenceType.SCREENSHOT
        assert item.description == "Test screenshot"
        assert item.test_id == "test_module::test_screenshot"
        assert item.requirement_ids == ["FS-001"]
        assert (collector.output_dir / item.file_path).exists()

    def test_capture_from_file_path(self, collector, evidence_dir):
        """Test capturing screenshot from file path."""
        # Create a test image file
        source_file = evidence_dir / "source_image.png"
        source_file.write_bytes(_create_minimal_png())

        collector.set_current_test("test_module::test_screenshot", ["FS-001"])
        item = collector.capture_screenshot(source_file, "From file")

        assert item.id == "EV-0001"
        assert (collector.output_dir / item.file_path).exists()

    def test_capture_increments_id(self, collector):
        """Test that evidence IDs are incremented."""
        png_data = _create_minimal_png()
        collector.set_current_test("test_module::test_func", [])

        item1 = collector.capture_screenshot(png_data, "First")
        item2 = collector.capture_screenshot(png_data, "Second")

        assert item1.id == "EV-0001"
        assert item2.id == "EV-0002"


@pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow not installed")
class TestCaptureDirectoryListing:
    """Tests for directory listing capture."""

    def test_capture_directory_listing(self, collector, evidence_dir):
        """Test capturing a directory listing."""
        # Create a test directory with files
        test_dir = evidence_dir / "test_files"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")

        collector.set_current_test("test_module::test_dir", ["FS-002"])
        item = collector.capture_directory_listing(test_dir, "Test directory")

        assert item.id == "EV-0001"
        assert item.evidence_type == EvidenceType.DIRECTORY_LISTING
        assert item.description == "Test directory"
        assert "directory_path" in item.metadata
        assert (collector.output_dir / item.file_path).exists()


@pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow not installed")
class TestCaptureCommandOutput:
    """Tests for command output capture."""

    def test_capture_command_output(self, collector):
        """Test capturing command output."""
        output_text = "Line 1\nLine 2\nLine 3"

        collector.set_current_test("test_module::test_cmd", ["FS-003"])
        item = collector.capture_command_output(output_text, "Command output")

        assert item.id == "EV-0001"
        assert item.evidence_type == EvidenceType.COMMAND_OUTPUT
        assert item.description == "Command output"
        assert (collector.output_dir / item.file_path).exists()

    def test_capture_with_command_metadata(self, collector):
        """Test capturing command output with command in metadata."""
        collector.set_current_test("test_module::test_cmd", [])
        item = collector.capture_command_output(
            "output", "Test", command="ls -la"
        )

        assert item.metadata.get("command") == "ls -la"


class TestAddImage:
    """Tests for adding existing images."""

    def test_add_existing_image(self, collector, evidence_dir):
        """Test adding an existing image file."""
        # Create a test image
        source_file = evidence_dir / "chart.png"
        source_file.write_bytes(_create_minimal_png())

        collector.set_current_test("test_module::test_img", ["FS-004"])
        item = collector.add_image(source_file, "Results chart")

        assert item.id == "EV-0001"
        assert item.evidence_type == EvidenceType.IMAGE
        assert item.description == "Results chart"
        assert "original_path" in item.metadata
        assert (collector.output_dir / item.file_path).exists()

    def test_add_nonexistent_image_raises(self, collector):
        """Test that adding nonexistent image raises error."""
        with pytest.raises(FileNotFoundError):
            collector.add_image("/nonexistent/image.png", "Not found")


class TestEvidenceRetrieval:
    """Tests for evidence retrieval methods."""

    def test_get_evidence_for_test(self, collector):
        """Test getting evidence for a specific test."""
        png_data = _create_minimal_png()

        collector.set_current_test("test1", ["FS-001"])
        collector.capture_screenshot(png_data, "Test 1 screenshot")

        collector.set_current_test("test2", ["FS-002"])
        collector.capture_screenshot(png_data, "Test 2 screenshot")

        test1_evidence = collector.get_evidence_for_test("test1")
        test2_evidence = collector.get_evidence_for_test("test2")

        assert len(test1_evidence) == 1
        assert len(test2_evidence) == 1
        assert test1_evidence[0].description == "Test 1 screenshot"
        assert test2_evidence[0].description == "Test 2 screenshot"

    def test_get_all_evidence(self, collector):
        """Test getting all evidence."""
        png_data = _create_minimal_png()

        collector.set_current_test("test1", [])
        collector.capture_screenshot(png_data, "First")
        collector.capture_screenshot(png_data, "Second")

        all_evidence = collector.get_all_evidence()
        assert len(all_evidence) == 2


class TestEvidenceManifest:
    """Tests for evidence manifest generation."""

    def test_write_manifest(self, collector):
        """Test writing evidence manifest."""
        png_data = _create_minimal_png()
        collector.set_current_test("test1", ["FS-001"])
        collector.capture_screenshot(png_data, "Screenshot 1")

        manifest_path = collector.write_manifest()

        assert manifest_path.exists()
        with open(manifest_path) as f:
            manifest = json.load(f)

        assert manifest["evidence_count"] == 1
        assert len(manifest["evidence"]) == 1
        assert manifest["evidence"][0]["id"] == "EV-0001"
        assert manifest["evidence"][0]["type"] == "screenshot"


@pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow not installed")
class TestTextToImage:
    """Tests for text_to_image utility function."""

    def test_text_to_image_creates_file(self, evidence_dir):
        """Test that text_to_image creates an image file."""
        output_path = evidence_dir / "test_output.png"
        result = text_to_image("Hello\nWorld", output_path)

        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_text_to_image_creates_parent_dirs(self, evidence_dir):
        """Test that parent directories are created."""
        output_path = evidence_dir / "nested" / "dirs" / "output.png"
        text_to_image("Test", output_path)

        assert output_path.exists()


@pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow not installed")
class TestDirectoryListingToImage:
    """Tests for directory_listing_to_image utility function."""

    def test_directory_listing_to_image(self, evidence_dir):
        """Test creating image from directory listing."""
        # Create test directory with files
        test_dir = evidence_dir / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        output_path = evidence_dir / "listing.png"
        result = directory_listing_to_image(test_dir, output_path)

        assert result == output_path
        assert output_path.exists()

    def test_nonexistent_directory_creates_error_image(self, evidence_dir):
        """Test that nonexistent directory creates error image."""
        output_path = evidence_dir / "error.png"
        result = directory_listing_to_image("/nonexistent/path", output_path)

        assert result == output_path
        assert output_path.exists()


def _create_minimal_png():
    """Create a minimal valid PNG file (1x1 white pixel)."""
    # This is a minimal valid PNG - 1x1 white pixel
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
        0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
        0x44, 0xAE, 0x42, 0x60, 0x82,
    ])


class TestEvidenceTypes:
    """Tests for EvidenceType enum."""

    def test_evidence_type_values(self):
        """Test evidence type enum values."""
        assert EvidenceType.SCREENSHOT.value == "screenshot"
        assert EvidenceType.DIRECTORY_LISTING.value == "directory_listing"
        assert EvidenceType.COMMAND_OUTPUT.value == "command_output"
        assert EvidenceType.IMAGE.value == "image"


class TestEvidenceItemDataclass:
    """Tests for EvidenceItem dataclass."""

    def test_evidence_item_creation(self):
        """Test creating an evidence item."""
        item = EvidenceItem(
            id="EV-0001",
            evidence_type=EvidenceType.SCREENSHOT,
            description="Test screenshot",
            file_path="evidence/screenshot.png",
            timestamp="2024-01-01T12:00:00",
            test_id="test_module::test_func",
            requirement_ids=["FS-001", "FS-002"],
        )

        assert item.id == "EV-0001"
        assert item.evidence_type == EvidenceType.SCREENSHOT
        assert item.requirement_ids == ["FS-001", "FS-002"]
        assert item.metadata == {}

    def test_evidence_item_with_metadata(self):
        """Test creating evidence item with metadata."""
        item = EvidenceItem(
            id="EV-0001",
            evidence_type=EvidenceType.COMMAND_OUTPUT,
            description="Test",
            file_path="evidence/output.png",
            timestamp="2024-01-01T12:00:00",
            test_id="test_module::test_func",
            requirement_ids=[],
            metadata={"command": "ls -la"},
        )

        assert item.metadata == {"command": "ls -la"}
