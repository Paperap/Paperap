#!/bin/bash
# Script to build the Paperap documentation

# Create necessary directories
mkdir -p docs/api

# Generate API documentation
cd docs
python generate_api_docs.py

echo "Documentation built successfully!"
echo "Open docs/_build/html/index.html to view the documentation."
