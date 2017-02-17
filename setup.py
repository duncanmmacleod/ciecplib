#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2015)
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

import os
import subprocess
import hashlib
import sys

from setuptools import (find_packages, setup)
from setuptools.command import (build_py, egg_info)
from distutils import log
from distutils.cmd import Command
from distutils.dist import Distribution

PACKAGENAME = 'ligo-dot-org'
PROVIDES = 'ligo.org'
AUTHOR = 'Duncan Macleod'
AUTHOR_EMAIL = 'duncan.macleod@ligo.org'
LICENSE = 'GPLv3'

# -- versioning ---------------------------------------------------------------

import versioneer
__version__ = versioneer.get_version()
cmdclass = versioneer.get_cmdclass()

# -- setup --------------------------------------------------------------------

packagenames = find_packages()
requires = ['kerberos', 'six', 'lxml']

setup(
    # distribution metadata
    name=PACKAGENAME,
    provides=[PROVIDES],
    version=__version__,
    description="A python client for LIGO.ORG-authenticated HTTP requests",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    url='https://github.com/duncanmmacleod/ligo.org/',
    # package metadata
    packages=packagenames,
    namespace_packages=['ligo'],
    include_package_data=True,
    cmdclass=cmdclass,
    requires=requires,
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Physics'
    ],
)
