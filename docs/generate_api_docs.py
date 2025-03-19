#!/usr/bin/env python3
"""
Script to automatically generate API documentation for Paperap.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def main():
    """Generate API documentation for Paperap."""
    # Get the docs directory
    docs_dir = Path(__file__).parent.absolute()
    api_dir = docs_dir / "api"

    # Create the api directory if it doesn't exist
    if api_dir.exists():
        shutil.rmtree(api_dir)
    api_dir.mkdir(exist_ok=True)

    # Change to the docs directory
    os.chdir(docs_dir)

    # Run sphinx-apidoc to generate the API documentation
    subprocess.run([
        "sphinx-apidoc",
        "-o",
        "api",
        "../src/paperap",
        "--separate",
        "--module-first",
        "--force",
    ], check=True)

    # Build the documentation
    subprocess.run([
        "sphinx-build",
        "-b",
        "html",
        ".",
        "_build/html",
    ], check=True)

    print("Documentation built successfully!")
    print(f"Open {docs_dir / '_build' / 'html' / 'index.html'} to view the documentation.")

if __name__ == "__main__":
    main()
