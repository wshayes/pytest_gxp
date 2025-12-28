"""Objective evidence capture for GxP validation."""

import base64
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from .markdown_format import EvidenceItem, EvidenceType

# Try to import Pillow, but make it optional
try:
    from PIL import Image, ImageDraw, ImageFont

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


def _get_font(size: int = 14) -> "ImageFont.FreeTypeFont":
    """Get a monospace font for rendering text."""
    # Try common monospace fonts
    font_names = [
        "DejaVuSansMono.ttf",
        "Menlo.ttc",
        "Monaco.dfont",
        "Consolas.ttf",
        "Courier New.ttf",
        "FreeMono.ttf",
    ]

    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue

    # Fall back to default font
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def text_to_image(
    text: str,
    output_path: Union[str, Path],
    font_size: int = 14,
    padding: int = 20,
    background_color: str = "#FFFFFF",
    text_color: str = "#000000",
    max_width: int = 1200,
) -> Path:
    """
    Convert text to a PNG image.

    Args:
        text: The text to render
        output_path: Path to save the output image
        font_size: Font size in pixels
        padding: Padding around the text
        background_color: Background color (hex)
        text_color: Text color (hex)
        max_width: Maximum image width

    Returns:
        Path to the created image

    Raises:
        ImportError: If Pillow is not installed
    """
    if not PILLOW_AVAILABLE:
        raise ImportError(
            "Pillow is required for text_to_image. Install with: pip install pytest-gxp[evidence]"
        )

    output_path = Path(output_path)
    font = _get_font(font_size)

    # Split text into lines
    lines = text.split("\n")

    # Calculate image dimensions
    if font:
        # Use textbbox for accurate text measurement
        dummy_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        line_heights = []
        line_widths = []
        for line in lines:
            if line:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_widths.append(bbox[2] - bbox[0])
                line_heights.append(bbox[3] - bbox[1])
            else:
                line_heights.append(font_size)
                line_widths.append(0)
        max_line_width = max(line_widths) if line_widths else 0
        line_height = max(line_heights) if line_heights else font_size
    else:
        # Estimate for default font
        max_line_width = max(len(line) * 8 for line in lines) if lines else 0
        line_height = font_size + 4

    width = min(max_line_width + padding * 2, max_width)
    height = len(lines) * (line_height + 2) + padding * 2

    # Create image
    img = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(img)

    # Draw text
    y = padding
    for line in lines:
        if font:
            draw.text((padding, y), line, fill=text_color, font=font)
        else:
            draw.text((padding, y), line, fill=text_color)
        y += line_height + 2

    # Save image
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


def directory_listing_to_image(
    directory_path: Union[str, Path],
    output_path: Union[str, Path],
    include_hidden: bool = True,
    **kwargs,
) -> Path:
    """
    Convert a directory listing to an image.

    Args:
        directory_path: Path to the directory to list
        output_path: Path to save the output image
        include_hidden: Whether to include hidden files (ls -a)
        **kwargs: Additional arguments passed to text_to_image

    Returns:
        Path to the created image
    """
    directory_path = Path(directory_path)

    # Build ls command
    ls_args = ["ls", "-la" if include_hidden else "-l"]
    ls_args.append(str(directory_path))

    try:
        result = subprocess.run(
            ls_args, capture_output=True, text=True, check=True, timeout=10
        )
        listing_text = result.stdout
    except subprocess.CalledProcessError as e:
        listing_text = f"Error listing directory: {e.stderr}"
    except subprocess.TimeoutExpired:
        listing_text = "Error: Directory listing timed out"
    except FileNotFoundError:
        listing_text = f"Error: Directory not found: {directory_path}"

    # Add header with directory path
    header = f"Directory: {directory_path}\n{'=' * 60}\n\n"
    full_text = header + listing_text

    return text_to_image(full_text, output_path, **kwargs)


def _generate_short_hash() -> str:
    """Generate a short random hash for unique filenames."""
    import random

    return hashlib.md5(str(random.random()).encode()).hexdigest()[:8]


class EvidenceCollector:
    """Collects objective evidence during test execution."""

    def __init__(self, output_dir: Union[str, Path], generate_thumbnails: bool = True):
        """
        Initialize the evidence collector.

        Args:
            output_dir: Base directory for evidence files (e.g., gxp_report_files)
            generate_thumbnails: Whether to generate thumbnail images
        """
        self.output_dir = Path(output_dir)
        self.evidence_dir = self.output_dir / "evidence"
        self.thumbnails_dir = self.evidence_dir / "thumbnails"
        self.generate_thumbnails = generate_thumbnails

        # Create directories
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        if generate_thumbnails:
            self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

        # Evidence storage
        self._evidence_items: List[EvidenceItem] = []
        self._evidence_counter = 0

        # Current test context
        self._current_test_id: Optional[str] = None
        self._current_requirement_ids: List[str] = []

    def set_current_test(self, test_id: str, requirement_ids: List[str]) -> None:
        """Set the current test context for evidence capture."""
        self._current_test_id = test_id
        self._current_requirement_ids = requirement_ids.copy() if requirement_ids else []

    def clear_current_test(self) -> None:
        """Clear the current test context."""
        self._current_test_id = None
        self._current_requirement_ids = []

    def _next_evidence_id(self) -> str:
        """Generate the next evidence ID."""
        self._evidence_counter += 1
        return f"EV-{self._evidence_counter:04d}"

    def _generate_filename(self, evidence_type: EvidenceType, extension: str = "png") -> str:
        """Generate a unique filename for evidence."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_hash = _generate_short_hash()
        return f"{evidence_type.value}_{timestamp}_{short_hash}.{extension}"

    def _create_thumbnail(self, image_path: Path) -> Optional[Path]:
        """Create a thumbnail for an image."""
        if not self.generate_thumbnails or not PILLOW_AVAILABLE:
            return None

        try:
            thumb_filename = f"thumb_{image_path.name}"
            thumb_path = self.thumbnails_dir / thumb_filename

            with Image.open(image_path) as img:
                img.thumbnail((200, 150), Image.Resampling.LANCZOS)
                img.save(thumb_path, "PNG")

            return thumb_path
        except Exception:
            return None

    def _add_evidence(
        self,
        evidence_type: EvidenceType,
        file_path: Path,
        description: str,
        metadata: Optional[Dict] = None,
    ) -> EvidenceItem:
        """Add an evidence item to the collection."""
        evidence_id = self._next_evidence_id()
        timestamp = datetime.now().isoformat()

        # Create thumbnail
        thumbnail_path = self._create_thumbnail(file_path)

        # Create relative paths for storage
        relative_file_path = file_path.relative_to(self.output_dir)
        relative_thumb_path = (
            thumbnail_path.relative_to(self.output_dir) if thumbnail_path else None
        )

        item = EvidenceItem(
            id=evidence_id,
            evidence_type=evidence_type,
            description=description,
            file_path=str(relative_file_path),
            timestamp=timestamp,
            test_id=self._current_test_id or "unknown",
            requirement_ids=self._current_requirement_ids.copy(),
            thumbnail_path=str(relative_thumb_path) if relative_thumb_path else None,
            metadata=metadata or {},
        )

        self._evidence_items.append(item)
        return item

    def capture_screenshot(
        self,
        image_data: Union[bytes, str, Path],
        description: str,
        metadata: Optional[Dict] = None,
    ) -> EvidenceItem:
        """
        Capture a screenshot as evidence.

        Args:
            image_data: Screenshot data as bytes, base64 string, or file path
            description: Description of the screenshot
            metadata: Optional additional metadata

        Returns:
            The created EvidenceItem
        """
        filename = self._generate_filename(EvidenceType.SCREENSHOT)
        file_path = self.evidence_dir / filename

        if isinstance(image_data, bytes):
            # Raw bytes
            file_path.write_bytes(image_data)
        elif isinstance(image_data, Path) or (
            isinstance(image_data, str) and os.path.exists(image_data)
        ):
            # File path - copy the file
            shutil.copy2(image_data, file_path)
        elif isinstance(image_data, str):
            # Try as base64
            try:
                decoded = base64.b64decode(image_data)
                file_path.write_bytes(decoded)
            except Exception as err:
                raise ValueError(
                    "image_data must be bytes, a file path, or base64-encoded string"
                ) from err
        else:
            raise ValueError(
                "image_data must be bytes, a file path, or base64-encoded string"
            )

        return self._add_evidence(EvidenceType.SCREENSHOT, file_path, description, metadata)

    def capture_directory_listing(
        self,
        directory_path: Union[str, Path],
        description: str,
        include_hidden: bool = True,
        metadata: Optional[Dict] = None,
    ) -> EvidenceItem:
        """
        Capture a directory listing as evidence.

        Args:
            directory_path: Path to the directory to list
            description: Description of the evidence
            include_hidden: Whether to include hidden files
            metadata: Optional additional metadata

        Returns:
            The created EvidenceItem
        """
        filename = self._generate_filename(EvidenceType.DIRECTORY_LISTING)
        file_path = self.evidence_dir / filename

        directory_listing_to_image(
            directory_path, file_path, include_hidden=include_hidden
        )

        evidence_metadata = {"directory_path": str(directory_path)}
        if metadata:
            evidence_metadata.update(metadata)

        return self._add_evidence(
            EvidenceType.DIRECTORY_LISTING, file_path, description, evidence_metadata
        )

    def capture_command_output(
        self,
        text: str,
        description: str,
        command: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> EvidenceItem:
        """
        Capture command or text output as evidence.

        Args:
            text: The text output to capture
            description: Description of the evidence
            command: Optional command that produced the output
            metadata: Optional additional metadata

        Returns:
            The created EvidenceItem
        """
        filename = self._generate_filename(EvidenceType.COMMAND_OUTPUT)
        file_path = self.evidence_dir / filename

        # Add command header if provided
        if command:
            header = f"Command: {command}\n{'=' * 60}\n\n"
            text = header + text

        text_to_image(text, file_path)

        evidence_metadata = {}
        if command:
            evidence_metadata["command"] = command
        if metadata:
            evidence_metadata.update(metadata)

        return self._add_evidence(
            EvidenceType.COMMAND_OUTPUT, file_path, description, evidence_metadata
        )

    def add_image(
        self,
        image_path: Union[str, Path],
        description: str,
        metadata: Optional[Dict] = None,
    ) -> EvidenceItem:
        """
        Add an existing image as evidence.

        Args:
            image_path: Path to the image file
            description: Description of the evidence
            metadata: Optional additional metadata

        Returns:
            The created EvidenceItem
        """
        source_path = Path(image_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Determine extension from source file
        extension = source_path.suffix.lstrip(".") or "png"
        filename = self._generate_filename(EvidenceType.IMAGE, extension)
        file_path = self.evidence_dir / filename

        shutil.copy2(source_path, file_path)

        evidence_metadata = {"original_path": str(source_path)}
        if metadata:
            evidence_metadata.update(metadata)

        return self._add_evidence(EvidenceType.IMAGE, file_path, description, evidence_metadata)

    def get_evidence_for_test(self, test_id: str) -> List[EvidenceItem]:
        """Get all evidence items for a specific test."""
        return [item for item in self._evidence_items if item.test_id == test_id]

    def get_all_evidence(self) -> List[EvidenceItem]:
        """Get all collected evidence items."""
        return self._evidence_items.copy()

    def write_manifest(self) -> Path:
        """Write the evidence manifest to a JSON file."""
        manifest_path = self.output_dir / "evidence_manifest.json"

        manifest_data = {
            "generated_at": datetime.now().isoformat(),
            "evidence_count": len(self._evidence_items),
            "evidence": [
                {
                    "id": item.id,
                    "type": item.evidence_type.value,
                    "description": item.description,
                    "file_path": item.file_path,
                    "timestamp": item.timestamp,
                    "test_id": item.test_id,
                    "requirement_ids": item.requirement_ids,
                    "thumbnail_path": item.thumbnail_path,
                    "metadata": item.metadata,
                }
                for item in self._evidence_items
            ],
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return manifest_path
