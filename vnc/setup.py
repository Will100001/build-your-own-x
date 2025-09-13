#!/usr/bin/env python3
"""
Setup script for VNC Server and Viewer
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="vnc-server-viewer",
    version="1.0.0",
    author="Build Your Own X",
    author_email="",
    description="A VNC Server and Viewer implementation from scratch",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/codecrafters-io/build-your-own-x",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Networking",
        "Topic :: Desktop Environment :: Screen Savers",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
        ],
        "docs": [
            "sphinx>=3.0.0",
            "sphinx-rtd-theme>=0.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "vnc-server=server.vnc_server:main",
            "vnc-viewer=viewer.vnc_viewer:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
)