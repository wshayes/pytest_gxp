# Specification Format

The Pytest GxP plugin uses Markdown files to define specifications. This standardized format makes it easy to create, maintain, and version control your requirements.

## File Structure

Each specification file should follow this structure:

```markdown
# Specification Title

## Version: X.Y

### FS-001: Requirement Title

#### Description
Detailed description of the requirement.

1. First requirement detail
2. Second requirement detail
...

Expected Result: What should happen when this requirement is met.

#### Metadata
Priority: High/Medium/Low
Category: Category Name
Owner: Owner Name
```

Use the appropriate prefix for your specification type: `IS-XXX` for Installation, `DS-XXX` for Design, `FS-XXX` for Functional, or `US-XXX` for User specifications.

## Specification Types

### Installation Specifications (IS)

Installation specifications define the requirements for proper installation, configuration, and deployment of the system.

**File naming**: Files containing "installation" in the filename (e.g., `installation_specification.md`)

**Requirement ID format**: `IS-XXX` (e.g., `IS-001`, `IS-002`)

**Used in**: IQ (Installation Qualification)

**Typical requirements include**:

- System prerequisites (OS, hardware, dependencies)
- Database installation and configuration
- Application file deployment
- Environment configuration
- Service registration
- Backup configuration

### Design Specifications (DS)

Design specifications define the architectural and design aspects of the system.

**File naming**: Files containing "design" in the filename (e.g., `design_specification.md`)

**Requirement ID format**: `DS-XXX` (e.g., `DS-001`, `DS-002`)

**Used in**: OQ (Operational Qualification)

### Functional Specifications (FS)

Functional specifications define how the system should behave from a functional perspective.

**File naming**: Files containing "functional" in the filename (e.g., `functional_specification.md`)

**Requirement ID format**: `FS-XXX` (e.g., `FS-001`, `FS-002`)

**Used in**: OQ (Operational Qualification)

### User Specifications (US)

User specifications define what users need from the system.

**File naming**: Files containing "user" in the filename (e.g., `user_specification.md`)

**Requirement ID format**: `US-XXX` (e.g., `US-001`, `US-002`)

**Used in**: PQ (Performance Qualification)

## Requirement Sections

### Requirement Header

```markdown
### FS-001: Requirement Title
```

- Must start with `###` or `##`
- Must include requirement ID with appropriate prefix (`IS-XXX`, `DS-XXX`, `FS-XXX`, or `US-XXX`)
- Must include a title after the colon

### Description Section

```markdown
#### Description
Detailed description here.

1. First point
2. Second point
```

The description can include:
- Plain text
- Numbered lists
- Bullet points
- Expected results

### Metadata Section (Optional)

```markdown
#### Metadata
Priority: High
Category: Security
Owner: Security Team
```

Metadata is stored as key-value pairs and can be used for filtering and reporting.

## Best Practices

1. **Use consistent ID formats**: Stick to your chosen format (IS-XXX, DS-XXX, FS-XXX, US-XXX)
2. **Write clear descriptions**: Be specific about what the requirement entails
3. **Include expected results**: Help testers understand the success criteria
4. **Version your specs**: Update the version number when making changes
5. **Use metadata**: Add relevant metadata for better organization
6. **Match specs to qualification type**: Use IS for IQ, DS/FS for OQ, US for PQ

## Examples

See the [Examples section](../examples/overview.md) for complete specification examples.

