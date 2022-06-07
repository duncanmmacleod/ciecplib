# -*- coding: utf-8 -*-
# Copyright (C) Cardiff University (2020-2022)
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

"""Environment defaults for ciecplib

This module parses the following environment variables to set default
settings for CIECP tools:

``ECP_IDP``
   the name or URL of the default ECP Identity Provider (IdP)

Defaults may also be parsed from the ``CIGETCERTOPTS`` environment
variable to support legacy users of ``cigetcert``.
"""

import argparse
import os

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


def _parse_cigetcertops():
    """Parse the ``CIGETCERTOPTS`` variable for known options

    Returns
    -------
    opts : `dict`
        a dict of options parsed from the variable
    """
    try:
        opts = os.environ["CIGETCERTOPTS"]
    except KeyError:
        return {}
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--institution")
    args, _ = parser.parse_known_args(opts.split())
    return vars(args)


def _get_default_idp():
    """Returns the default ECP IdP, or `None` if no default is found
    """
    try:
        return os.environ["ECP_IDP"]
    except KeyError:
        return _parse_cigetcertops().get("institution")


DEFAULT_IDP = _get_default_idp()
