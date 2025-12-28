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

    def test_parse_directory(self, temp_dir, sample_design_spec_content, sample_functional_spec_content):
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

