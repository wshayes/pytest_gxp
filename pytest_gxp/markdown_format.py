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
REQUIREMENT_DESCRIPTION_PATTERN = r"^####?\s+Description\s*$"
METADATA_PATTERN = r"^####?\s+Metadata\s*$"
SPEC_HEADER_PATTERN = r"^#\s+(?P<title>.+)\s*$"
SPEC_VERSION_PATTERN = r"^##\s+Version\s*:\s*(?P<version>.+)$"
