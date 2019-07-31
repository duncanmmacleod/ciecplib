# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2019)
#
# This file is part of LIGO.ORG.
#
# LIGO.ORG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LIGO.ORG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LIGO.ORG.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import re

from setuptools import (find_packages, setup)

PACKAGENAME = 'ligo.org'
PROVIDES = 'ligo.org'
AUTHOR = 'Duncan Macleod'
AUTHOR_EMAIL = 'duncan.macleod@ligo.org'
LICENSE = 'GPLv3'


def find_version(path, varname="__version__"):
    """Parse the version metadata in the given file.
    """
    with open(path, 'r') as fp:
        version_file = fp.read()
    version_match = re.search(
        r"^{} = ['\"]([^'\"]*)['\"]".format(varname),
        version_file,
        re.M,
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup_requires = [
    "setuptools",
]
install_requires = [
    "lxml",
    "M2Crypto",
    "pathlib ; python_version < '3.4'",
    "pykerberos ; sys_platform != 'win32'",
    "pyOpenSSL",
    "winkerberos ; sys_platform == 'win32'",
]
tests_require = [
    "mock ; python_version < '3'",
    "pytest",
    "pytest-cov",
]
extras_require = {
    "test": tests_require,
    "doc": [
        "sphinx",
        "sphinx-argparse",
        "sphinx_automodapi",
        "sphinx_rtd_theme",
        "sphinx_tabs",
    ],
}


setup(
    # distribution metadata
    name="ligo.org",
    version=find_version(os.path.join("ligo", "org", "__init__.py")),
    author="Duncan Macleod <duncan.macleod@ligo.org>",
    author_email="duncan.macleod@ligo.org",
    license="GPL-3.0-or-later",
    description="A python client for LIGO.ORG SAML ECP authentication",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    url='https://github.com/duncanmmacleod/ligo.org/',
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Physics'
    ],
    # contents
    packages=find_packages(),
    namespace_packages=['ligo'],
    entry_points={
        "console_scripts": [
            "ligo-proxy-init=ligo.org.tool.ligo_proxy_init:main",
            "ligo-curl=ligo.org.tool.ligo_curl:main",
        ],
    },
    # dependencies
    setup_requires=setup_requires,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require,
)
