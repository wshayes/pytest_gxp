"""Setup configuration for pytest-gxp."""

from setuptools import find_packages, setup

setup(
    name="pytest-gxp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytest>=7.0.0",
        "click>=8.0.0",
    ],
    entry_points={
        "pytest11": [
            "gxp = pytest_gxp.plugin",
        ],
        "console_scripts": [
            "gxp_test_stubs = pytest_gxp.cli.test_stubs:main",
            "gxp_req_coverage = pytest_gxp.cli.req_coverage:main",
        ],
    },
    python_requires=">=3.8",
)
