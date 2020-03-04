# -*- coding: utf-8 -*-
# Copyright (C) Cardiff University (2019-2020)
#
# This file is part of ciecplib.
#
# ciecplib is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ciecplib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ciecplib.  If not, see <http://www.gnu.org/licenses/>.

"""Kerberos utilities for ciecplib
"""

import subprocess
from distutils.spawn import find_executable

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


def _find_executable(name):
    exe = find_executable(name)
    if exe is None:
        raise OSError("cannot find {0!r}".format(name))
    return exe


def has_credential(klist=None):
    """Run ``klist`` to determine whether a kerberos credential is available.

    Parameters
    ----------
    klist : `str`, optional
        path to the ``klist`` executable, defaults to searching ``$PATH``

    Returns
    ----------
    True
        if ``klist -s`` indicates a valid credential
    False
        otherwise (including klist failures)
    """
    # run klist to check credentials
    klist = klist or find_executable("klist")
    try:
        subprocess.check_output([klist, "-s"])
    except subprocess.CalledProcessError:
        return False
    return True
