"""Markdown format definitions for GxP specifications."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class SpecType(Enum):
    """Type of specification."""

    DESIGN = "Design"
    FUNCTIONAL = "Functional"
    USER = "User"
    INSTALLATION = "Installation"


class QualificationType(Enum):
    """Type of qualification phase (GAMP5)."""

    IQ = "Installation Qualification"
    OQ = "Operational Qualification"
    PQ = "Performance Qualification"


class EvidenceType(Enum):
    """Type of objective evidence."""

    SCREENSHOT = "screenshot"
    DIRECTORY_LISTING = "directory_listing"
    COMMAND_OUTPUT = "command_output"
    IMAGE = "image"
    UNSCRIPTED_SESSION = "unscripted_session"


# Evidence types whose stored file is an image and can be rendered inline in reports
IMAGE_EVIDENCE_TYPES = frozenset(
    {
        EvidenceType.SCREENSHOT,
        EvidenceType.DIRECTORY_LISTING,
        EvidenceType.COMMAND_OUTPUT,
        EvidenceType.IMAGE,
    }
)


@dataclass
class EvidenceItem:
    """An objective evidence item captured during testing."""

    id: str  # "EV-0001"
    evidence_type: EvidenceType
    description: str
    file_path: str  # Relative path to evidence file
    timestamp: str
    test_id: str  # pytest nodeid
    requirement_ids: List[str]
    thumbnail_path: Optional[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ApprovalSignature:
    """Approval signature for validation documents."""

    name: str
    role: str  # "Tester", "Reviewer", "Approver"
    date: str
    signature_placeholder: str = ""


@dataclass
class ValidationMetadata:
    """Metadata for validation report."""

    qualification_type: QualificationType
    software_name: str
    software_version: str
    project_name: str
    validation_date: str
    tester: Optional["ApprovalSignature"] = None
    reviewer: Optional["ApprovalSignature"] = None
    approver: Optional["ApprovalSignature"] = None


@dataclass(frozen=True)
class ValidationFinding:
    """A defect in the validation inputs (specifications, markers, evidence).

    ``code`` is a stable kebab-case identifier, e.g. ``duplicate-requirement-id``,
    ``malformed-requirement-heading``, ``unknown-requirement-ref``,
    ``uncovered-requirement``.
    """

    code: str
    severity: str  # "error" | "warning"
    message: str
    location: str = ""  # "file.md:21" or a pytest nodeid


@dataclass
class Requirement:
    """A requirement from a specification."""

    id: str
    title: str
    description: str
    spec_type: SpecType
    parent_id: Optional[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TestCase:
    """A test case derived from requirements."""

    id: str
    title: str
    description: str
    requirements: List[str]  # List of requirement IDs this test case covers
    steps: List[str]
    expected_result: str
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Specification:
    """A complete specification document."""

    spec_type: SpecType
    title: str
    version: str
    requirements: List[Requirement]
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# Markdown format patterns
REQUIREMENT_PATTERN = r"^###?\s+(?P<id>[A-Z]+-\d+)\s*:\s*(?P<title>.+)$"
# Matches anything that looks like it was meant to be a requirement heading; a line
# matching this but not REQUIREMENT_PATTERN is reported as malformed instead of parsed.
REQUIREMENT_HEADING_LOOSE_PATTERN = r"^###?\s+(?P<id>[A-Z]{2,}-\d+)\b"
REQUIREMENT_DESCRIPTION_PATTERN = r"^####?\s+Description\s*$"
METADATA_PATTERN = r"^####?\s+Metadata\s*$"
SPEC_HEADER_PATTERN = r"^#\s+(?P<title>.+)\s*$"
SPEC_VERSION_PATTERN = r"^##\s+Version\s*:\s*(?P<version>.+)$"
