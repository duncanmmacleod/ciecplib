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
        import ligo.org
        self.distribution.metadata.version = ligo.org.__version__
        desc, longdesc = ligo.org.__doc__.split('\n', 1)
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
# Generate portfile

class BuildPortfile(Command, GitVersionMixin):
    """Generate a Macports Portfile for this project from the current build
    """
    description = 'Generate Macports Portfile'
    user_options = [
        ('version=', None, 'the X.Y.Z package version'),
        ('portfile=', None, 'target output file, default: \'Portfile\''),
        ('template=', None,
         'Portfile template, default: \'Portfile.template\''),
    ]

    def initialize_options(self):
        self.version = None
        self.portfile = 'Portfile'
        self.template = 'Portfile.template'
        self._template = None

    def finalize_options(self):
        from jinja2 import Template
        with open(self.template, 'r') as t:
            self._template = Template(t.read())

    def run(self):
        # get version from distribution
        if self.version is None:
            try:
                self.update_metadata()
            except ImportError:
                self.run_command('sdist')
                self.update_metadata()
        # find dist file
        dist = os.path.join(
            'dist',
            '%s-%s.tar.gz' % (self.distribution.get_name(),
                              self.distribution.get_version()))
        # run sdist if needed
        if not os.path.isfile(dist):
            self.run_command('sdist')
            self.update_metadata()
        # get checksum digests
        log.info('reading distribution tarball %r' % dist)
        with open(dist, 'rb') as fobj:
            data = fobj.read()
        log.info('recovered digests:')
        digest = dict()
        digest['rmd160'] = self._get_rmd160(dist)
        for algo in [1, 256]:
            digest['sha%d' % algo] = self._get_sha(data, algo)
        for key, val in digest.iteritems():
            log.info('    %s: %s' % (key, val))
        # write finished portfile to file
        with open(self.portfile, 'w') as fport:
            fport.write(self._template.render(
                version=self.distribution.get_version(), **digest))
        log.info('portfile written to %r' % self.portfile)

    @staticmethod
    def _get_sha(data, algorithm=256):
        hash_ = getattr(hashlib, 'sha%d' % algorithm)
        return hash_(data).hexdigest()

    @staticmethod
    def _get_rmd160(filename):
        p = subprocess.Popen(['openssl', 'rmd160', filename],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            raise subprocess.CalledProcessError(err)
        else:
            return out.splitlines()[0].rsplit(' ', 1)[-1]

cmdclass['port'] = BuildPortfile


# -----------------------------------------------------------------------------
# Run setup

packagenames = find_packages()

requires = ['kerberos', 'six', 'lxml']

# don't use setup_requires if just checking for information
# (credit: matplotlib/setup.py)
setup_requires = []
if '--help' not in sys.argv and '--help-commands' not in sys.argv:
    dist_ = Distribution({'cmdclass': cmdclass})
    dist_.parse_config_files()
    dist_.parse_command_line()
    if not (any('--' + opt in sys.argv for opt in
                Distribution.display_option_names + ['help']) or
            dist_.commands == ['clean']):
        setup_requires = ['jinja2', 'gitpython']

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
    url='https://github.com/duncanmmacleod/ligo.org/',
    # package metadata
    packages=packagenames,
    namespace_packages=['ligo'],
    include_package_data=True,
    cmdclass=cmdclass,
    setup_requires=requires + setup_requires,
    requires=requires,
    use_2to3=False,
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
