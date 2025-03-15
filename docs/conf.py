# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

from pathlib import Path

from sphinx.ext.apidoc import main as apidoc_main

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

from ciecplib import __version__ as ciecplib_version


# -- Project information -----------------------------------------------------

project = "ciecplib"
copyright = "2019, Duncan Macleod"
author = "Duncan Macleod"

# The full version, including alpha/beta/rc tags
release = ciecplib_version


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinxarg.ext",
    "sphinx_automodapi.automodapi",
    "sphinx_tabs.tabs",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path = ['_static']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "monokai"

# The reST default role (used for this markup: `text`) to use for all
# documents.
default_role = "obj"

# -- Extensions --------------------------------------------------------------

# Intersphinx directory
intersphinx_mapping = {
    "cryptography": ("https://cryptography.io/en/stable", None),
    "gssapi": ("https://pythongssapi.github.io/python-gssapi/", None),
    "python": ("https://docs.python.org/3/", None),
    "requests": ("https://requests.readthedocs.io/en/stable/", None),
    "requests_ecp": ("https://requests-ecp.readthedocs.io/en/stable/", None),
}

# napoleon configuration
napoleon_use_rtype = False

# Don't inherit in automodapi
numpydoc_show_class_members = False
automodapi_inherited_members = False


# -- run sphinx-apidoc automatically ------------------------------------------
# this is required to have apidoc generated as part of readthedocs builds
# see https://github.com/rtfd/readthedocs.org/issues/1139

def run_apidoc(_):
    """Call sphinx-apidoc
    """
    curdir = Path(__file__).parent
    apidir = curdir / "api"
    module = curdir.parent / "ciecplib"
    apidoc_main([
        str(module),
        str(module / "tool"),
        str(module / "tests"),
        "--force",
        "--implicit-namespaces",
        "--module-first",
        "--no-toc",
        "--output-dir", str(apidir),
        "--separate",
    ])


# -- setup --------------------------------------------------------------------

def setup(app):
    app.connect("builder-inited", run_apidoc)
