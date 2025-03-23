
# Configuration file for the Sphinx documentation builder.
import os
import sys
from datetime import datetime

# Add the project root directory to the path so Sphinx can find the modules
sys.path.insert(0, os.path.abspath('../src'))

# Project information
project = 'Paperap'
copyright = f'{datetime.now().year}, Jess Mann'
author = 'Jess Mann'

# The full version, including alpha/beta/rc tags
release = '0.0.8'
version = release

# Add any Sphinx extension module names here
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosectionlabel',
    'sphinx_autodoc_typehints',
    'myst_parser',
]

# Add any paths that contain templates here
templates_path = ['_templates']

# List of patterns to exclude from source files
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The theme to use for HTML and HTML Help pages
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 4,
    'titles_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'style_nav_header_background': '#2980B9',
    # Read the Docs specific options
    'logo_only': False,
    'analytics_id': '',  # Provided by Read the Docs as needed
}

# Add any paths that contain custom static files
html_static_path = ['_static']

# Add custom JavaScript files
html_js_files = [
    ("readthedocs.js", {"defer": "defer"}),
]

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
    'pydantic': ('https://docs.pydantic.dev/latest/', None),
}

# Set the canonical URL to prevent duplicate content issues
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "/")

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = None
napoleon_attr_annotations = True

# AutoDoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}

# TypeHints settings
typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True

# MyST Parser settings
myst_enable_extensions = [
    'colon_fence',
    'deflist',
]
myst_heading_anchors = 3
