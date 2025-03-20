Contributing
===========

We welcome contributions to Paperap!

Development Setup
----------------

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/Paperap/Paperap.git
      cd Paperap

2. Install development dependencies:

   .. code-block:: bash

      pip install -e ".[dev]"

3. Set up pre-commit hooks:

   .. code-block:: bash

      pre-commit install

Running Tests
------------

Run tests using pytest:

.. code-block:: bash

   pytest

Code Style
---------

This project uses:

- Black for code formatting
- Ruff for linting
- MyPy for type checking

You can run these tools with:

.. code-block:: bash

   black src tests
   ruff check src tests
   mypy src
