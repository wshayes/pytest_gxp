"""Markdown specification parser for GxP specifications."""

import re
from pathlib import Path
from typing import Dict, List, Tuple

from .markdown_format import (
    REQUIREMENT_HEADING_LOOSE_PATTERN,
    REQUIREMENT_PATTERN,
    SPEC_HEADER_PATTERN,
    SPEC_VERSION_PATTERN,
    Requirement,
    Specification,
    SpecType,
    ValidationFinding,
)


class SpecificationParser:
    """Parser for Markdown-based GxP specifications."""

    def __init__(self):
        self.requirement_pattern = re.compile(REQUIREMENT_PATTERN, re.IGNORECASE)
        self.loose_requirement_pattern = re.compile(REQUIREMENT_HEADING_LOOSE_PATTERN)
        self.spec_header_pattern = re.compile(SPEC_HEADER_PATTERN)
        self.spec_version_pattern = re.compile(SPEC_VERSION_PATTERN, re.IGNORECASE)
        self.findings: List[ValidationFinding] = []
        # requirement id -> (filename, title, line number) of its first definition
        self._seen_requirements: Dict[str, Tuple[str, str, int]] = {}

    def parse_file(self, file_path: Path) -> Specification:
        """Parse a specification file and return a Specification object."""
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Determine spec type from filename
        spec_type = self._detect_spec_type(file_path.name)

        # Parse the content
        lines = content.split("\n")
        title = self._extract_title(lines)
        version = self._extract_version(lines)
        located = self._extract_requirements(lines, spec_type, file_path.name)
        self._record_duplicates(located, file_path.name)

        return Specification(
            spec_type=spec_type,
            title=title,
            version=version,
            requirements=[req for req, _ in located],
        )

    def _record_duplicates(self, located: List[Tuple[Requirement, int]], filename: str) -> None:
        """Report requirement IDs defined more than once, across all parsed files."""
        for req, line_no in located:
            first = self._seen_requirements.get(req.id)
            if first is None:
                self._seen_requirements[req.id] = (filename, req.title, line_no)
                continue

            first_file, first_title, first_line = first
            self.findings.append(
                ValidationFinding(
                    code="duplicate-requirement-id",
                    severity="error",
                    message=(
                        f"Requirement {req.id} is defined more than once: "
                        f"{first_file}:{first_line} ('{first_title}') and "
                        f"{filename}:{line_no} ('{req.title}')"
                    ),
                    location=f"{filename}:{line_no}",
                )
            )

    def _detect_spec_type(self, filename: str) -> SpecType:
        """Detect specification type from filename."""
        filename_lower = filename.lower()
        if "design" in filename_lower:
            return SpecType.DESIGN
        elif "functional" in filename_lower:
            return SpecType.FUNCTIONAL
        elif "user" in filename_lower:
            return SpecType.USER
        elif "installation" in filename_lower:
            return SpecType.INSTALLATION
        else:
            # Default to functional if unclear
            return SpecType.FUNCTIONAL

    def _extract_title(self, lines: List[str]) -> str:
        """Extract title from the first H1 header."""
        for line in lines:
            match = self.spec_header_pattern.match(line.strip())
            if match:
                return match.group("title").strip()
        return "Untitled Specification"

    def _extract_version(self, lines: List[str]) -> str:
        """Extract version from version header."""
        for line in lines:
            match = self.spec_version_pattern.match(line.strip())
            if match:
                return match.group("version").strip()
        return "1.0"

    def _extract_requirements(
        self, lines: List[str], spec_type: SpecType, filename: str = ""
    ) -> List[Tuple[Requirement, int]]:
        """Extract requirements from markdown content, each with its 1-based line number.

        Headings that look like requirements but do not match the required
        ``### ID: Title`` form are reported as findings and not parsed.
        """
        requirements: List[Tuple[Requirement, int]] = []
        current_requirement = None
        current_line = 0
        current_description = []
        in_description = False
        in_metadata = False
        current_metadata = {}

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Check for requirement header
            match = self.requirement_pattern.match(line_stripped)
            if match:
                # Save previous requirement if exists
                if current_requirement:
                    current_requirement.description = "\n".join(current_description).strip()
                    if current_metadata:
                        current_requirement.metadata = current_metadata.copy()
                    requirements.append((current_requirement, current_line))

                # Start new requirement
                req_id = match.group("id")
                req_title = match.group("title")
                current_requirement = Requirement(
                    id=req_id, title=req_title, description="", spec_type=spec_type
                )
                current_line = i + 1
                current_description = []
                current_metadata = {}
                in_description = False
                in_metadata = False
                continue

            # A heading that only looks like a requirement is a defect, not a requirement
            if self.loose_requirement_pattern.match(line_stripped):
                self.findings.append(
                    ValidationFinding(
                        code="malformed-requirement-heading",
                        severity="error",
                        message=(
                            "Requirement heading does not match the required "
                            f"'### ID: Title' form: {line_stripped}"
                        ),
                        location=f"{filename}:{i + 1}",
                    )
                )
                continue

            # Check for description section
            if line_stripped.lower().startswith("####") and "description" in line_stripped.lower():
                in_description = True
                in_metadata = False
                continue

            # Check for metadata section
            if line_stripped.lower().startswith("####") and "metadata" in line_stripped.lower():
                in_description = False
                in_metadata = True
                continue

            # Collect description content
            if current_requirement:
                if in_description:
                    if line_stripped and not line_stripped.startswith("#"):
                        current_description.append(line)
                elif in_metadata:
                    if ":" in line_stripped:
                        key, value = line_stripped.split(":", 1)
                        current_metadata[key.strip()] = value.strip()
                elif not line_stripped.startswith("#"):
                    # Content before explicit description section
                    current_description.append(line)

        # Save last requirement
        if current_requirement:
            current_requirement.description = "\n".join(current_description).strip()
            if current_metadata:
                current_requirement.metadata = current_metadata.copy()
            requirements.append((current_requirement, current_line))

        return requirements

    def parse_directory(self, directory: Path) -> Dict[SpecType, Specification]:
        """Parse all specification files in a directory."""
        specs = {}
        self.findings = []
        self._seen_requirements = {}
        for file_path in sorted(directory.glob("*.md")):
            try:
                spec = self.parse_file(file_path)
                specs[spec.spec_type] = spec
            except Exception as e:
                print(f"Warning: Failed to parse {file_path}: {e}")
        return specs
