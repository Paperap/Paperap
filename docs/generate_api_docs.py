
#!/usr/bin/env python3
"""
Script to automatically generate API documentation for Paperap.
"""

import os
import shutil
import subprocess # nosec B404
import sys
import shlex
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
    sphinx_apidoc_path = shutil.which("sphinx-apidoc")
    if not sphinx_apidoc_path:
        print("Error: sphinx-apidoc not found in PATH", file=sys.stderr)
        sys.exit(1)

    subprocess.run([
        sphinx_apidoc_path,
        "-o",
        "api",
        "../src/paperap",
        "--separate",
        "--module-first",
        "--force",
    ], check=True, text=True) # nosec B603 # args are trusted

    # Create modules directory if it doesn't exist
    modules_dir = docs_dir / "modules"
    modules_dir.mkdir(exist_ok=True)

    # Create any missing module documentation files
    for module_name in ["client", "models", "resources", "signals", "plugins", "exceptions"]:
        module_path = modules_dir / f"{module_name}.rst"
        if not module_path.exists():
            with open(module_path, "w") as f:
                f.write(f"""
{module_name.capitalize()}
{'=' * len(module_name)}

This section contains documentation for the {module_name} module.

.. automodule:: paperap.{module_name}
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
""")

    # Build the documentation
    sphinx_build_path = shutil.which("sphinx-build")
    if not sphinx_build_path:
        print("Error: sphinx-build not found in PATH", file=sys.stderr)
        sys.exit(1)

    subprocess.run([
        sphinx_build_path,
        "-b",
        "html",
        ".",
        "_build/html",
    ], check=True, text=True) # nosec B603 # args are trusted

    print("Documentation built successfully!")
    print(f"Open {docs_dir / '_build' / 'html' / 'index.html'} to view the documentation.")

if __name__ == "__main__":
    main()
