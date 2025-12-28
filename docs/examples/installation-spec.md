# Installation Specification Example

This is an example Installation Specification (IS) for a GxP-validated application. Installation specifications define the requirements for proper installation, configuration, and deployment of the system.

## Purpose

The Installation Specification is used during **Installation Qualification (IQ)** to verify that:

- Software is installed correctly
- System requirements are met
- Configuration is properly applied
- Dependencies are available
- Environment is correctly set up

## Example Installation Specification

Create a file named `installation_specification.md` in your `gxp_spec_files/` directory:

```markdown
# Installation Specification

## Version: 1.0

### IS-001: System Requirements

#### Description
The system shall verify that all minimum system requirements are met before installation.

1. Python version 3.8 or higher must be installed
2. Operating system must be Windows 10+, macOS 12+, or Ubuntu 20.04+
3. Minimum 4GB RAM available
4. Minimum 1GB disk space available

Expected Result: System requirements verification passes without errors.

#### Metadata
Priority: Critical
Category: Prerequisites
Phase: IQ

### IS-002: Database Installation

#### Description
The database server shall be installed and configured correctly.

1. PostgreSQL 14+ must be installed
2. Database service must be running
3. Database user must be created with appropriate permissions
4. Database schema must be initialized

Expected Result: Database is accessible and schema is correctly applied.

#### Metadata
Priority: High
Category: Database
Phase: IQ

### IS-003: Application Installation

#### Description
The application shall be installed in the designated directory.

1. Application files must be copied to /opt/myapp (Linux) or C:\MyApp (Windows)
2. Configuration files must be present in config/ subdirectory
3. Log directory must be created with write permissions
4. Application binary must be executable

Expected Result: Application files are installed with correct permissions.

#### Metadata
Priority: High
Category: Application
Phase: IQ

### IS-004: Environment Configuration

#### Description
The application environment shall be properly configured.

1. Environment variables must be set (APP_HOME, APP_ENV, DATABASE_URL)
2. SSL certificates must be installed in the trust store
3. Network ports 8080 and 8443 must be available
4. Firewall rules must allow application traffic

Expected Result: Environment is configured for application operation.

#### Metadata
Priority: High
Category: Configuration
Phase: IQ

### IS-005: Service Registration

#### Description
The application shall be registered as a system service.

1. Service must be registered with systemd (Linux) or Windows Services
2. Service must be configured for automatic startup
3. Service must have appropriate resource limits configured
4. Service account must have minimum required permissions

Expected Result: Service is registered and can be started/stopped via system tools.

#### Metadata
Priority: Medium
Category: Service
Phase: IQ

### IS-006: Backup Configuration

#### Description
Backup systems shall be configured for the application.

1. Backup directory must exist with sufficient space
2. Backup schedule must be configured (daily at 02:00)
3. Backup retention policy must be set (30 days)
4. Backup restoration procedure must be documented

Expected Result: Backup system is operational and tested.

#### Metadata
Priority: Medium
Category: Backup
Phase: IQ
```

## Writing IQ Tests

Link your IQ tests to installation requirements:

```python
import subprocess
import sys
import os
import pytest

@pytest.mark.gxp
@pytest.mark.requirements(["IS-001"])
def test_python_version(gxp_evidence):
    """Verify Python version meets requirements."""
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

    gxp_evidence.capture_command_output(
        f"Python version: {version_str}",
        "Python version check"
    )

    assert version_info >= (3, 8), f"Python 3.8+ required, found {version_str}"


@pytest.mark.gxp
@pytest.mark.requirements(["IS-002"])
def test_database_connection(gxp_evidence):
    """Verify database is accessible."""
    import psycopg2

    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]

        gxp_evidence.capture_command_output(
            f"Database connection successful\nVersion: {version}",
            "Database connection test"
        )

        cursor.close()
        conn.close()
        assert True
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")


@pytest.mark.gxp
@pytest.mark.requirements(["IS-003"])
def test_application_files(gxp_evidence):
    """Verify application files are installed."""
    from pathlib import Path

    app_home = Path(os.environ.get("APP_HOME", "/opt/myapp"))

    required_files = [
        app_home / "bin" / "app",
        app_home / "config" / "app.yaml",
        app_home / "config" / "logging.yaml",
    ]

    gxp_evidence.capture_directory_listing(
        app_home,
        "Application installation directory"
    )

    for file_path in required_files:
        assert file_path.exists(), f"Required file missing: {file_path}"


@pytest.mark.gxp
@pytest.mark.requirements(["IS-004"])
def test_environment_variables(gxp_evidence):
    """Verify environment variables are configured."""
    required_vars = ["APP_HOME", "APP_ENV", "DATABASE_URL"]

    env_status = []
    for var in required_vars:
        value = os.environ.get(var)
        status = "SET" if value else "MISSING"
        env_status.append(f"{var}: {status}")

    gxp_evidence.capture_command_output(
        "\n".join(env_status),
        "Environment variable check"
    )

    for var in required_vars:
        assert os.environ.get(var), f"Environment variable {var} not set"


@pytest.mark.gxp
@pytest.mark.requirements(["IS-005"])
def test_service_status(gxp_evidence):
    """Verify service is registered and running."""
    result = subprocess.run(
        ["systemctl", "status", "myapp"],
        capture_output=True,
        text=True
    )

    gxp_evidence.capture_command_output(
        result.stdout,
        "Service status",
        command="systemctl status myapp"
    )

    assert "active (running)" in result.stdout.lower(), "Service is not running"
```

## Requirement ID Format

Installation Specification requirements use the `IS-XXX` format:

- `IS-001` - System requirements
- `IS-002` - Database installation
- `IS-003` - Application installation

## Related Specifications

| Spec Type | ID Format | Purpose |
|-----------|-----------|---------|
| Design (DS) | `DS-XXX` | How the system is designed |
| Functional (FS) | `FS-XXX` | What the system does |
| User (US) | `US-XXX` | What the user needs |
| **Installation (IS)** | `IS-XXX` | How to install the system |

## Best Practices

1. **Be Specific**: Include exact version numbers, paths, and configuration values
2. **Automate Verification**: Write tests that can automatically verify installation
3. **Capture Evidence**: Use `gxp_evidence` to document the installation state
4. **Include Rollback**: Document how to uninstall or rollback if needed
5. **Version Control**: Keep the installation specification under version control

## Running IQ Tests

```bash
pytest --gxp \
    --gxp-qualification-type=IQ \
    --gxp-spec-files=gxp_spec_files \
    --gxp-report-files=gxp_report_files \
    --gxp-project-name="My Application" \
    --gxp-software-version="1.0.0"
```

## See Also

- [Design Specification](design-spec.md)
- [Functional Specification](functional-spec.md)
- [User Specification](user-spec.md)
- [Running Tests](../user-guide/running-tests.md)
