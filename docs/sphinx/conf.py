"""Sphinx config for Mintlify SDK reference (JSON builder)."""

from __future__ import annotations

import os
import sys

# Package root: distribution/clients/python/modus-sdk/
sys.path.insert(0, os.path.abspath("../.."))

project = "Python SDK"
author = "Modus"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]
# Keep types in the signature code fence only — putting [str] in prose breaks Mintlify MDX.
autodoc_typehints = "signature"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": False,
    "member-order": "bysource",
}
add_module_names = False
napoleon_google_docstrings = True
napoleon_numpy_docstrings = False
napoleon_use_param = True
napoleon_use_rtype = True
exclude_patterns = ["_build"]
html_theme = "alabaster"
nitpicky = False
