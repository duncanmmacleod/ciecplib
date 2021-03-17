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

import re
import subprocess
from distutils.spawn import find_executable

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"

KLIST_EXE = find_executable("klist")
KLIST_PRINCIPAL_RE = re.compile(
    r"\nDefault principal: ([\w\.@]+)",
    re.M,
)


def _find_executable(name):
    exe = find_executable(name)
    if exe is None:
        raise OSError("cannot find {0!r}".format(name))
    return exe


def has_credential(klist=KLIST_EXE):
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
    klist = klist or _find_executable("klist")
    try:
        subprocess.check_output([klist, "-s"])
    except subprocess.CalledProcessError:
        return False
    return True


def find_principal(klist=KLIST_EXE):
    """Determine the default principal for an active kerberos credential

    Parameters
    ----------
    klist : `str`, optional
        path to the ``klist`` executable, defaults to searching ``$PATH``
    """
    klist = klist or _find_executable("klist")
    out = subprocess.check_output([klist]).decode("utf-8")
    try:
        return KLIST_PRINCIPAL_RE.search(out).groups()[0]
    except (AttributeError, IndexError):  # failed to parse principal
        raise RuntimeError("failed to parse principal from `klist` output")
