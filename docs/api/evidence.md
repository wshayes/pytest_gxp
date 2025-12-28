# Evidence API

The evidence module provides tools for capturing objective evidence during GxP validation tests.

## EvidenceCollector

The `EvidenceCollector` class manages evidence capture and storage.

### Constructor

```python
EvidenceCollector(output_dir: Path, generate_thumbnails: bool = True)
```

**Parameters**:

- `output_dir`: Base directory for evidence files
- `generate_thumbnails`: Whether to generate thumbnail images (default: True)

### Methods

#### `set_current_test(test_id: str, requirement_ids: List[str]) -> None`

Set the current test context for evidence capture.

**Parameters**:

- `test_id`: pytest node ID of the current test
- `requirement_ids`: List of requirement IDs associated with the test

#### `clear_current_test() -> None`

Clear the current test context.

#### `capture_screenshot(image_data, description: str) -> EvidenceItem`

Capture a screenshot as evidence.

**Parameters**:

- `image_data`: Image data (bytes, file path, or base64 string)
- `description`: Description of the evidence

**Returns**: `EvidenceItem` with auto-generated ID (e.g., `EV-0001`)

#### `capture_directory_listing(directory_path, description: str) -> EvidenceItem`

Capture a directory listing as an image.

**Parameters**:

- `directory_path`: Path to the directory
- `description`: Description of the evidence

**Returns**: `EvidenceItem`

**Requires**: `pip install pytest-gxp[evidence]` (Pillow)

#### `capture_command_output(text: str, description: str, command: str = None) -> EvidenceItem`

Capture command output as an image.

**Parameters**:

- `text`: Text output to capture
- `description`: Description of the evidence
- `command`: Optional command that produced the output (stored in metadata)

**Returns**: `EvidenceItem`

**Requires**: `pip install pytest-gxp[evidence]` (Pillow)

#### `add_image(image_path, description: str) -> EvidenceItem`

Add an existing image file as evidence.

**Parameters**:

- `image_path`: Path to the image file
- `description`: Description of the evidence

**Returns**: `EvidenceItem`

**Raises**: `FileNotFoundError` if image doesn't exist

#### `get_evidence_for_test(test_id: str) -> List[EvidenceItem]`

Get all evidence items for a specific test.

**Parameters**:

- `test_id`: pytest node ID

**Returns**: List of `EvidenceItem` objects

#### `get_all_evidence() -> List[EvidenceItem]`

Get all captured evidence items.

**Returns**: List of `EvidenceItem` objects

#### `write_manifest() -> Path`

Write evidence manifest JSON file.

**Returns**: Path to the manifest file

## EvidenceItem

Data class for evidence metadata.

### Attributes

- `id`: Auto-generated ID (e.g., `EV-0001`)
- `evidence_type`: `EvidenceType` enum value
- `description`: Description of the evidence
- `file_path`: Relative path to evidence file
- `timestamp`: ISO timestamp of capture
- `test_id`: pytest node ID of the test
- `requirement_ids`: List of associated requirement IDs
- `thumbnail_path`: Optional path to thumbnail image
- `metadata`: Optional dictionary of additional metadata

## EvidenceType

Enum for evidence types.

- `EvidenceType.SCREENSHOT` - Screenshot image
- `EvidenceType.DIRECTORY_LISTING` - Directory listing converted to image
- `EvidenceType.COMMAND_OUTPUT` - Command output converted to image
- `EvidenceType.IMAGE` - Existing image file

## Utility Functions

### `text_to_image(text: str, output_path: Path, font_size: int = 14) -> Path`

Convert text to a PNG image.

**Parameters**:

- `text`: Text to render
- `output_path`: Path for output image
- `font_size`: Font size in pixels (default: 14)

**Returns**: Path to the created image

**Requires**: Pillow

### `directory_listing_to_image(directory_path, output_path: Path) -> Path`

Convert directory listing to a PNG image.

**Parameters**:

- `directory_path`: Path to directory
- `output_path`: Path for output image

**Returns**: Path to the created image

**Requires**: Pillow

## Fixture Usage

The `gxp_evidence` fixture is the recommended way to capture evidence in tests:

```python
import pytest

@pytest.mark.gxp
@pytest.mark.requirements(["FS-001"])
def test_application_login(gxp_evidence, driver):
    """Test login with evidence capture."""

    # Capture a screenshot (from Selenium, Playwright, etc.)
    gxp_evidence.capture_screenshot(
        driver.get_screenshot_as_png(),
        "Login screen displayed"
    )

    # Perform login
    driver.find_element("id", "username").send_keys("user")
    driver.find_element("id", "password").send_keys("pass")
    driver.find_element("id", "submit").click()

    # Capture another screenshot
    gxp_evidence.capture_screenshot(
        driver.get_screenshot_as_png(),
        "Login successful - dashboard displayed"
    )
```

### Evidence Methods Summary

| Method | Description | Requires Pillow |
|--------|-------------|-----------------|
| `capture_screenshot(data, description)` | Capture screenshot | No |
| `capture_directory_listing(path, description)` | Directory listing to image | Yes |
| `capture_command_output(text, description)` | Text to image | Yes |
| `add_image(path, description)` | Add existing image | No |

## Programmatic Usage

```python
from pathlib import Path
from pytest_gxp.evidence import (
    EvidenceCollector,
    text_to_image,
    directory_listing_to_image,
)

# Create collector
collector = EvidenceCollector(Path("reports"), generate_thumbnails=True)

# Set test context
collector.set_current_test("test_module::test_func", ["FS-001"])

# Capture evidence
item = collector.capture_screenshot(screenshot_bytes, "Login screen")
print(f"Evidence ID: {item.id}")  # EV-0001

# Clear context
collector.clear_current_test()

# Write manifest
collector.write_manifest()

# Utility functions
text_to_image("Command output here", Path("output.png"))
directory_listing_to_image("/app/config", Path("config_listing.png"))
```
