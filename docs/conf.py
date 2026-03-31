# docs/conf.py
from __future__ import annotations

import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

# Avoid autosummary name collision between package attribute `aas_creo_bridge.app.main`
# and submodule `aas_creo_bridge.app.main`.
try:
    _app_pkg = importlib.import_module("aas_creo_bridge.app")
    if hasattr(_app_pkg, "main"):
        delattr(_app_pkg, "main")
except Exception:
    pass

project = "AAS-Creo-Bridge"
author = "Your Team"
copyright = ""
language = "en"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
    "sphinx_simplepdf",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

autoclass_content = "both"  # class docstring + __init__ docstring
autodoc_member_order = "bysource"  # follow source order (often nicer)
autodoc_typehints = "description"  # show type hints in the description, not signatures
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

autosummary_generate = True

templates_path = ["_templates"]
exclude_patterns: list[str] = []

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# PDF (LaTeX) output settings
latex_engine = "pdflatex"
latex_documents = [
    ("index", "AAS-Creo-Bridge.tex", "AAS-Creo-Bridge Documentation", author, "manual"),
]
latex_elements = {
    "papersize": "a4paper",
    "pointsize": "11pt",
    "extraclassoptions": "openany,oneside",
    "maketitle": r"""\input{custom_cover.inc}
\input{erklaerung.inc}""",
    "preamble": r"""\fvset{samepage=true}""",
}
latex_additional_files = [
    "custom_cover.inc",
    "erklaerung.inc",
    "_images/HKA_MMT_Wortmarke_RGB.jpg",
    "_images/HKA_MMT_Bildmarke-h_RGB.jpg",
    "_images/Titelbild.png",
]
