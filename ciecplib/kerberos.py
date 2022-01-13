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

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"

KLIST_EXE = "klist"
KLIST_PRINCIPAL_RE = re.compile(
    r"\nDefault principal: ([\w\.@]+)",
    re.M,
)


def has_credential(*args, klist=KLIST_EXE):
    """Run ``klist`` to determine whether a kerberos credential is available.

    Parameters
    ----------
    *args : `str`, optional
        extra arguments to pass to ``klist``, note that the ``-s`` option
        is always passed to ``klist``

    klist : `str`, optional
        path to the ``klist`` executable

    Returns
    -------
    True
        if ``klist -s`` indicates a valid credential
    False
        otherwise (including klist failures)

    Examples
    --------
    >>> has_credential()
    False
    >>> has_credential("mykrb5cc", klist="/opt/special/bin/klist")
    True

    See also
    --------
    klist(1)
        for details of options accepted by ``klist``
    """
    # run klist to check credentials
    try:
        subprocess.check_output([klist, "-s"] + list(args))
    except subprocess.CalledProcessError:
        return False
    return True


def find_principal(*args, klist=KLIST_EXE):
    """Determine the default principal for an active kerberos credential

    Parameters
    ----------
    klist : `str`, optional
        path to the ``klist`` executable, defaults to searching ``$PATH``
    """
    out = subprocess.check_output([klist] + list(args)).decode("utf-8")
    try:
        return KLIST_PRINCIPAL_RE.search(out).groups()[0]
    except (AttributeError, IndexError):  # failed to parse principal
        raise RuntimeError("failed to parse principal from `klist` output")


def realm(principal):
    """Return the kerbeos realm name from a principal

    Parameters
    ----------
    principal : `str`
        the kerberos principal to parse

    Returns
    -------
    realm : `str`
        the realm name

    Examples
    --------
    >>> realm('marie.curie@EXAMPLE.ORG')
    'EXAMPLE.ORG'
    """
    try:
        user, realm = principal.rsplit("@", 1)
    except ValueError as exc:  # no "@" character
        exc.args = (
            f"invalid kerberos principal '{principal}'",
        )
        raise
    return realm
