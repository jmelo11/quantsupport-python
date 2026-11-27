"""Independent binding guides, computational studies, and exact API references."""

import sys
from pathlib import Path

import tomllib

sys.path.insert(0, str(Path(__file__).resolve().parent / "_ext"))

from api_navigation import DOMAIN_TITLES, generate_python_navigation, python_sections
from python_api import (
    class_declaration,
    construction_note,
    constructor_signature,
    declaration_source,
    method_signature,
    prepare_class_docstrings,
    public_annotation,
    public_signature,
)

ROOT = Path(__file__).resolve().parents[1]

project = "QuantSupport Python"
author = "QuantSupport contributors"
release = tomllib.loads((ROOT / "Cargo.toml").read_text())["workspace"]["package"][
    "version"
]
extensions = ["autoapi.extension", "sphinx.ext.napoleon", "myst_nb", "notebook_studies"]

autoapi_dirs = [str(ROOT / "python" / "quantsupport")]
autoapi_template_dir = "_templates/autoapi"
autoapi_file_patterns = ["*.pyi"]
autoapi_own_page_level = "class"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]
autoapi_python_class_content = "class"
autoapi_member_order = "groupwise"
autoapi_add_toctree_entry = False
napoleon_numpy_docstring = True
napoleon_google_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True
html_theme = "furo"
html_title = f"QuantSupport Python {release}"
html_baseurl = "https://jmelo11.github.io/quantsupport-python/"
html_show_sourcelink = False
html_static_path = ["_static"]
html_css_files = ["notebook-tables.css"]
exclude_patterns = [
    "_build",
    "_templates/**",
    "README.md",
    "requirements.txt",
]
nb_execution_mode = "off"
myst_enable_extensions = ["dollarmath", "amsmath"]

PUBLIC_PROTOCOLS = {
    "__enter__",
    "__exit__",
    "__iter__",
    "__len__",
    "__getitem__",
    "__add__",
    "__radd__",
    "__sub__",
    "__rsub__",
    "__mul__",
    "__rmul__",
    "__truediv__",
    "__rtruediv__",
    "__neg__",
}


def skip_internal(app, what, name, obj, skip, options):
    member = name.rsplit(".", 1)[-1]
    if member in PUBLIC_PROTOCOLS:
        return False
    if member.startswith("_"):
        return True
    return None


def setup(app):
    app.connect("autoapi-skip-member", skip_internal)
    app.connect("autodoc-process-docstring", prepare_class_docstrings, priority=100)
    app.connect("builder-inited", generate_python_navigation)


def prepare_templates(environment):
    environment.filters["constructor_signature"] = constructor_signature
    environment.filters["class_declaration"] = class_declaration
    environment.filters["construction_note"] = construction_note
    environment.filters["declaration_source"] = declaration_source
    environment.filters["public_signature"] = public_signature
    environment.filters["public_annotation"] = public_annotation
    environment.filters["method_signature"] = method_signature
    environment.filters["python_sections"] = python_sections
    environment.filters["domain_title"] = DOMAIN_TITLES.__getitem__


autoapi_prepare_jinja_env = prepare_templates

core_revision = tomllib.loads((ROOT / "Cargo.toml").read_text())["dependencies"][
    "quantsupport"
]["rev"]
rst_epilog = f".. |core_revision| replace:: {core_revision}"
