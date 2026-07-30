"""Tests for the specification parser."""

from pytest_gxp.markdown_format import SpecType
from pytest_gxp.parser import SpecificationParser


class TestSpecificationParser:
    """Test cases for SpecificationParser."""

    def test_parse_file_design_spec(self, sample_design_spec_file):
        """Test parsing a design specification file."""
        parser = SpecificationParser()
        spec = parser.parse_file(sample_design_spec_file)

        assert spec.spec_type == SpecType.DESIGN
        assert spec.title == "Design Specification"
        assert spec.version == "1.0"
        assert len(spec.requirements) == 1
        assert spec.requirements[0].id == "DS-001"
        assert spec.requirements[0].title == "User Authentication"

    def test_parse_file_functional_spec(self, sample_functional_spec_file):
        """Test parsing a functional specification file."""
        parser = SpecificationParser()
        spec = parser.parse_file(sample_functional_spec_file)

        assert spec.spec_type == SpecType.FUNCTIONAL
        assert spec.title == "Functional Specification"
        assert spec.version == "1.0"
        assert len(spec.requirements) == 1
        assert spec.requirements[0].id == "FS-001"

    def test_parse_file_user_spec(self, sample_user_spec_file):
        """Test parsing a user specification file."""
        parser = SpecificationParser()
        spec = parser.parse_file(sample_user_spec_file)

        assert spec.spec_type == SpecType.USER
        assert spec.title == "User Specification"
        assert spec.version == "1.0"
        assert len(spec.requirements) == 1
        assert spec.requirements[0].id == "US-001"

    def test_detect_spec_type_design(self):
        """Test detecting design specification type."""
        parser = SpecificationParser()
        assert parser._detect_spec_type("design_spec.md") == SpecType.DESIGN
        assert parser._detect_spec_type("Design_Specification.md") == SpecType.DESIGN

    def test_detect_spec_type_functional(self):
        """Test detecting functional specification type."""
        parser = SpecificationParser()
        assert parser._detect_spec_type("functional_spec.md") == SpecType.FUNCTIONAL
        assert parser._detect_spec_type("Functional_Spec.md") == SpecType.FUNCTIONAL

    def test_detect_spec_type_user(self):
        """Test detecting user specification type."""
        parser = SpecificationParser()
        assert parser._detect_spec_type("user_spec.md") == SpecType.USER
        assert parser._detect_spec_type("User_Specification.md") == SpecType.USER

    def test_detect_spec_type_default(self):
        """Test default specification type when unclear."""
        parser = SpecificationParser()
        # Should default to functional
        assert parser._detect_spec_type("unknown.md") == SpecType.FUNCTIONAL

    def test_extract_title(self):
        """Test extracting title from markdown."""
        parser = SpecificationParser()
        lines = ["# My Specification Title", "## Version: 1.0"]
        title = parser._extract_title(lines)
        assert title == "My Specification Title"

    def test_extract_title_missing(self):
        """Test extracting title when missing."""
        parser = SpecificationParser()
        lines = ["## Version: 1.0", "Some content"]
        title = parser._extract_title(lines)
        assert title == "Untitled Specification"

    def test_extract_version(self):
        """Test extracting version from markdown."""
        parser = SpecificationParser()
        lines = ["# Title", "## Version: 2.1"]
        version = parser._extract_version(lines)
        assert version == "2.1"

    def test_extract_version_missing(self):
        """Test extracting version when missing."""
        parser = SpecificationParser()
        lines = ["# Title", "Some content"]
        version = parser._extract_version(lines)
        assert version == "1.0"

    def test_extract_requirements(self, sample_functional_spec_content, temp_dir):
        """Test extracting requirements from markdown."""
        parser = SpecificationParser()
        file_path = temp_dir / "test_spec.md"
        file_path.write_text(sample_functional_spec_content)

        spec = parser.parse_file(file_path)
        assert len(spec.requirements) == 1
        req = spec.requirements[0]
        assert req.id == "FS-001"
        assert req.title == "User Login"
        assert "Display login form" in req.description
        assert req.metadata.get("Priority") == "High"

    def test_parse_directory(
        self, temp_dir, sample_design_spec_content, sample_functional_spec_content
    ):
        """Test parsing a directory of specification files."""
        parser = SpecificationParser()

        # Create spec files
        (temp_dir / "design_specification.md").write_text(sample_design_spec_content)
        (temp_dir / "functional_specification.md").write_text(sample_functional_spec_content)

        specs = parser.parse_directory(temp_dir)

        assert SpecType.DESIGN in specs
        assert SpecType.FUNCTIONAL in specs
        assert specs[SpecType.DESIGN].title == "Design Specification"
        assert specs[SpecType.FUNCTIONAL].title == "Functional Specification"

    def test_parse_directory_empty(self, temp_dir):
        """Test parsing an empty directory."""
        parser = SpecificationParser()
        specs = parser.parse_directory(temp_dir)
        assert len(specs) == 0

    def test_parse_file_with_metadata(self, temp_dir):
        """Test parsing file with metadata section."""
        content = """# Test Spec

## Version: 1.0

### REQ-001: Test Requirement

#### Description
This is a test requirement.

#### Metadata
Priority: High
Category: Testing
Owner: Test Team
"""
        file_path = temp_dir / "test_spec.md"
        file_path.write_text(content)

        parser = SpecificationParser()
        spec = parser.parse_file(file_path)

        assert len(spec.requirements) == 1
        req = spec.requirements[0]
        assert req.metadata["Priority"] == "High"
        assert req.metadata["Category"] == "Testing"
        assert req.metadata["Owner"] == "Test Team"

    def test_parse_file_multiple_requirements(self, temp_dir):
        """Test parsing file with multiple requirements."""
        content = """# Test Spec

## Version: 1.0

### REQ-001: First Requirement

#### Description
First requirement description.

### REQ-002: Second Requirement

#### Description
Second requirement description.
"""
        file_path = temp_dir / "test_spec.md"
        file_path.write_text(content)

        parser = SpecificationParser()
        spec = parser.parse_file(file_path)

        assert len(spec.requirements) == 2
        assert spec.requirements[0].id == "REQ-001"
        assert spec.requirements[1].id == "REQ-002"


class TestParserFindings:
    """Test cases for validation findings raised while parsing."""

    def test_duplicate_requirement_id_across_files(self, temp_dir):
        """A requirement ID defined in two files is reported once, keeping both definitions."""
        (temp_dir / "design_specification.md").write_text(
            "# Design Spec\n\n## Version: 1.0\n\n### SH-001: Shared In Design\n\nDesign text.\n"
        )
        (temp_dir / "functional_specification.md").write_text(
            "# Functional Spec\n\n## Version: 1.0\n\n### SH-001: Shared In Functional\n\nText.\n"
        )

        parser = SpecificationParser()
        specs = parser.parse_directory(temp_dir)

        duplicates = [f for f in parser.findings if f.code == "duplicate-requirement-id"]
        assert len(duplicates) == 1
        finding = duplicates[0]
        assert finding.severity == "error"
        assert finding.location == "functional_specification.md:5"
        assert "design_specification.md:5" in finding.message
        assert "functional_specification.md:5" in finding.message

        # Both definitions survive in their own specifications
        assert [r.id for r in specs[SpecType.DESIGN].requirements] == ["SH-001"]
        assert [r.id for r in specs[SpecType.FUNCTIONAL].requirements] == ["SH-001"]

    def test_malformed_requirement_heading(self, temp_dir):
        """A heading missing the ': Title' part is reported and not parsed as a requirement."""
        content = """# Functional Spec

## Version: 1.0

### FS-001: Good Requirement

Fine.

### FS-002

Missing the title separator.
"""
        file_path = temp_dir / "functional_specification.md"
        file_path.write_text(content)

        parser = SpecificationParser()
        spec = parser.parse_file(file_path)

        assert [r.id for r in spec.requirements] == ["FS-001"]
        malformed = [f for f in parser.findings if f.code == "malformed-requirement-heading"]
        assert len(malformed) == 1
        assert malformed[0].severity == "error"
        assert malformed[0].location == "functional_specification.md:9"
        assert "### FS-002" in malformed[0].message

    def test_parse_directory_order_is_stable(self, temp_dir):
        """Requirements are parsed in filename order, and findings reset between runs."""
        for name in ("c_functional_spec.md", "a_design_spec.md", "b_user_spec.md"):
            (temp_dir / name).write_text(
                f"# {name}\n\n## Version: 1.0\n\n### DUP-001: Same Id Everywhere\n\nText.\n"
            )

        parser = SpecificationParser()
        first = parser.parse_directory(temp_dir)
        first_locations = [f.location for f in parser.findings]
        second = parser.parse_directory(temp_dir)
        second_locations = [f.location for f in parser.findings]

        assert list(first) == list(second)
        assert first_locations == second_locations
        # a_design_spec.md is seen first, so the later two files are the duplicates
        assert first_locations == ["b_user_spec.md:5", "c_functional_spec.md:5"]
