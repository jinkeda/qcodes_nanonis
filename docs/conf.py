# -*- coding: utf-8 -*-
"""
Sphinx configuration for QCoDeS Nanonis.
"""

import os
import sys

ROOT = os.path.abspath("..")
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, ROOT)
sys.path.insert(0, SRC)

project = "QCoDeS Nanonis"
author = "K. Jin"
copyright = "2026, K. Jin"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "sphinx_rtd_theme"
