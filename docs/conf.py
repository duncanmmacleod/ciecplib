"""Sphinx documentation configuration."""

from datetime import (
    datetime,
    timezone,
)

import sphinx_github_style

from ciecplib import __version__ as ciecplib_version

project = "ciecplib"
copyright = f"{datetime.now(tz=timezone.utc).date().year}, Cardiff University"
author = "Duncan Macleod"

# The full version, including alpha/beta/rc tags
release = ciecplib_version
version = release.split("+", 1)[0]

# -- content -------------------------

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- HTML formatting -----------------

html_theme = "furo"
html_title = f"{project} {version}"
html_static_path = ["_static"]
html_css_files = [
    "ciecplib.css",
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_dark_style = "monokai"

# The reST default role (used for this markup: `text`) to use for all
# documents.
default_role = "obj"

# -- extensions ----------------------

extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "sphinx.ext.napoleon",
    "sphinxarg.ext",
    "sphinx_automodapi.automodapi",
    "sphinx_copybutton",
    "sphinx_design",
]

# -- automodapi
automodapi_inherited_members = False

# -- intersphinx
intersphinx_mapping = {key: (value, None) for key, value in {
    "cryptography": "https://cryptography.io/en/stable",
    "gssapi": "https://pythongssapi.github.io/python-gssapi/",
    "python": "https://docs.python.org/3/",
    "requests": "https://requests.readthedocs.io/en/stable/",
    "requests_ecp": "https://requests-ecp.readthedocs.io/en/stable/",
}.items()}

# -- linkcode
linkcode_url = sphinx_github_style.get_linkcode_url(
    blob=sphinx_github_style.get_linkcode_revision("head"),
    url=f"https://git.ligo.org/computing/software/{project}",
)
linkcode_resolve = sphinx_github_style.get_linkcode_resolve(linkcode_url)

# -- napoleon
napoleon_use_rtype = False
