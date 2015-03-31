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

from distutils import log
from setuptools import (find_packages, setup)
from setuptools.command import (build_py, egg_info)

PACKAGENAME = 'ligo-dot-org'
PROVIDES = 'ligo.org'
AUTHOR = 'Duncan Macleod'
AUTHOR_EMAIL = 'duncan.macleod@ligo.org'
LICENSE = 'GPLv3'
VERSION_PY = os.path.join(PROVIDES.replace('.', '/'), 'version.py')

cmdclass = {}


# -----------------------------------------------------------------------------
# Custom builders to write version.py

class GitVersionMixin(object):
    """Mixin class to add methods to generate version information from git.
    """
    def write_version_py(self, pyfile):
        """Generate target file with versioning information from git VCS
        """
        log.info("generating %s" % pyfile)
        import vcs
        gitstatus = vcs.GitStatus()
        try:
            with open(pyfile, 'w') as fobj:
                gitstatus.write(fobj, author=AUTHOR, email=AUTHOR_EMAIL)
        except:
            if os.path.exists(pyfile):
                os.unlink(pyfile)
            raise
        return gitstatus

    def update_metadata(self):
        """Import package base and update distribution metadata
        """
        import cis
        self.distribution.metadata.version = cis.__version__
        desc, longdesc = cis.__doc__.split('\n', 1)
        self.distribution.metadata.description = desc
        self.distribution.metadata.long_description = longdesc.strip('\n')


class LigoDotOrgBuildPy(build_py.build_py, GitVersionMixin):
    """Custom build_py command to deal with version generation
    """
    def __init__(self, *args, **kwargs):
        build_py.build_py.__init__(self, *args, **kwargs)

    def run(self):
        try:
            self.write_version_py(VERSION_PY)
        except ImportError:
            raise
        except:
            if not os.path.isfile(VERSION_PY):
                raise
        self.update_metadata()
        build_py.build_py.run(self)

cmdclass['build_py']= LigoDotOrgBuildPy


class LigoDotOrgEggInfo(egg_info.egg_info, GitVersionMixin):
    """Custom egg_info command to deal with version generation
    """
    def finalize_options(self):
        try:
            self.write_version_py(VERSION_PY)
        except ImportError:
            raise
        except:
            if not os.path.isfile(VERSION_PY):
                raise
        if not self.distribution.metadata.version:
            self.update_metadata()
        egg_info.egg_info.finalize_options(self)

cmdclass['egg_info']= LigoDotOrgEggInfo


# -----------------------------------------------------------------------------
# Run setup

packagenames = find_packages()


setup(
    # distribution metadata
    name=PACKAGENAME,
    provides=[PROVIDES],
    version=None,
    description=None,
    long_description=None,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    url=None,
    # package metadata
    packages=packagenames,
    namespace_packages=['ligo'],
    include_package_data=True,
    cmdclass=cmdclass,
    setup_requires=[
    ],
    install_requires=[
    ],
    requires=[
        'kerberos',
    ],
    use_2to3=True,
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
