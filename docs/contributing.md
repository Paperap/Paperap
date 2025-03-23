# Contributing

Thank you for considering contributing to Paperap!

## Development Environment

1. Clone the repository:
   ```bash
   gh repo clone https://github.com/Paperap/Paperap.git
   cd paperap
   ```

2. Create a virtual environment and install development dependencies:
   ```bash
   uv venv .venv
   uv sync --all-groups
   source .venv/bin/activate
   ```

3. Define an .env file
   ```bash
   cp env-sample .env
   ```

Most common actions are defined in package.json scripts. You can run them using `bun run <script>`.

## Running Tests

```bash
bun run test
```

Integration tests are provided in the `tests/integration` directory. However, you may need to fiddle with them to get the data lined up with your Paperless-ngX instance. This will be improved in the future. You will probably want to run tests/lib/first_run.py to get some data in your Paperless-ngX instance. Be aware that it will FULLY DELETE all data in that instance first.

Hypothesis tests are located in `tests/unit/hypothesis`. These tests are run automatically with all unit tests. If you're not familiar with hypothesis, it is worth noting that it will run with slightly different parameters each time, and remember failures for future runs.

## Building Documentation

```bash
python docs/generate_api_docs.py
```

## Code Style

This project uses:
- ruff
- pre-commit
- mypy

It successfully passes pyright, mypy, and basedmypy with a fairly strict config in pyproject.toml. All future code should do the same.

## Submitting Changes

1. Create a new branch for your changes
2. Make your changes
3. Run the tests and ensure they pass
4. Run linters via `bun run pre-commit`, and github actions via `act`.
5. Update documentation if necessary
6. Submit a pull request
