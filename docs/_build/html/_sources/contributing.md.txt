# Contributing

Thank you for considering contributing to Paperap!

## Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/paperap.git
   cd paperap
   ```

2. Create a virtual environment and install development dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

## Running Tests

```bash
pytest
```

## Building Documentation

```bash
cd docs
python generate_api_docs.py
```

## Code Style

This project uses:
- Black for code formatting
- Isort for import sorting
- Mypy for type checking
- Pylint and Flake8 for linting

## Submitting Changes

1. Create a new branch for your changes
2. Make your changes
3. Run the tests and ensure they pass
4. Update documentation if necessary
5. Submit a pull request
