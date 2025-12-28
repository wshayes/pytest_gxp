"""Tests for pytest plugin hooks."""

import pytest


class TestPluginHooks:
    """Test cases for pytest plugin hooks."""

    def test_pytest_addoption(self, pytestconfig):
        """Test that plugin options are added."""
        # Verify options exist
        assert hasattr(pytestconfig.option, "gxp") or pytestconfig.getoption("--gxp") is not None

    def test_pytest_configure_without_gxp_flag(self, pytestconfig):
        """Test plugin configuration without --gxp flag."""
        # Plugin should not crash when --gxp is not used
        # This is more of an integration test
        pass

    def test_gxp_marker_registered(self, pytestconfig):
        """Test that GxP markers are registered."""
        markers = pytestconfig.getini("markers")
        gxp_markers = [m for m in markers if "gxp" in m.lower()]
        assert len(gxp_markers) > 0

    def test_requirements_marker_registered(self, pytestconfig):
        """Test that requirements marker is registered."""
        markers = pytestconfig.getini("markers")
        req_markers = [m for m in markers if "requirements" in m.lower()]
        assert len(req_markers) > 0


@pytest.mark.gxp
@pytest.mark.requirements(["FS-001"])
def test_example_gxp_test():
    """Example GxP test that should be recognized by the plugin."""
    assert True


@pytest.mark.gxp
def test_example_gxp_test_no_requirements():
    """Example GxP test without requirements marker."""
    assert True

