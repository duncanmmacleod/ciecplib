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

"""Common utilities for tools
"""

from __future__ import print_function

import argparse
import sys

from .. import __version__
from ..cookies import (
    LoadError,
    has_session_cookies,
    load_cookiejar,
)
from ..env import _get_default_idp
from ..utils import get_idps

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


# -- argparse helpers ---------------------------

class HelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = "Usage: "
        return super(HelpFormatter, self)._format_usage(
            usage,
            actions,
            groups,
            prefix,
        )


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        add_helpers = kwargs.pop("add_helpers", True)
        version = kwargs.pop("version", __version__)
        manpage = kwargs.pop("manpage", None)

        kwargs.setdefault("formatter_class", HelpFormatter)
        kwargs.setdefault("add_help", not add_helpers)
        super(ArgumentParser, self).__init__(*args, **kwargs)

        self._positionals.title = "Required arguments"
        self._optionals.title = "Options"

        # add manpage options for argparse-manpage
        self._manpage = manpage

        # add helper commands group
        if add_helpers:
            helpers = self.add_argument_group("Helper arguments")
            helpers.add_argument(
                "-h",
                "--help",
                action="help",
                default=argparse.SUPPRESS,
                help="show this help message and exit",
            )
            helpers.add_argument(
                "-l",
                "--list-idps",
                action=ListIdpsAction,
            )
            if version is not None:
                helpers.add_argument(
                    "-V",
                    "--version",
                    action="version",
                    version=version,
                )

    def add_identity_provider_argument(
            self,
            *args,
            **kwargs
    ):
        if not args:
            args = ("-i", "--identity-provider")
        kwargs.setdefault("default", _get_default_idp())
        kwargs.setdefault(
            "help",
            "name of institution providing the identity (e.g. 'Cardiff "
            "University'), or domain name of IdP host (e.g. idp.cf.ac.uk), "
            "see --list-idps for a list of Identity Provider (IdPs) and "
            "their IdP URL. "
            "Shortened institution names (e.g. 'Cardiff') can be given as "
            "long as they uniquely match a full institution name known by "
            "CILogon",
        )
        return super(ArgumentParser, self).add_argument(
            *args,
            **kwargs
        )


class ListIdpsAction(argparse.Action):
    def __init__(
            self,
            option_strings,
            dest=argparse.SUPPRESS,
            default=argparse.SUPPRESS,
            help="show IdP names and URLs and exit",
    ):
        super(ListIdpsAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        idps = get_idps()
        formatter = parser._get_formatter()
        fmt = "%-{0}r : %s".format(max(map(len, idps)) + 2)
        lines = []
        for pair in sorted(idps.items(), key=lambda x: x[0]):
            lines.append(fmt % pair)
        formatter.add_text('\n'.join(lines))
        parser._print_message(formatter.format_help(), sys.stdout)
        parser.exit()


# -- miscellaneous ------------------------------

def reuse_cookiefile(cookiefile, url, verbose=False):
    """Load cookies from a cookiefile and determine if they can be reused

    Parameters
    ----------
    cookiefile : `str`
        the path to the cookie file

    url : `str`
        the URL of the service being accessed with cookies

    verbose : `bool`, optional
        if `True`, print verbose output

    Returns
    -------
    cookiejar : `ligo.org.cookies.ECPCookieJar`, `NoneType`
        the cookie jar (if the cookie file was read correctly), otherwise
        `None`
    reuse : `bool`
        `True` if the cookies in the jar can be reused to access the given
        service URL, otherwise `False`
    """
    if verbose:
        print("Validating existing cookies...", end=" ")
    try:
        cookiejar = load_cookiejar(cookiefile, strict=True)
    except (LoadError, OSError):
        if verbose:
            print("failed to load cookie file")
        return None, None
    reuse = has_session_cookies(cookiejar, url)
    if verbose and reuse:
        print("OK")
    elif verbose:
        print("cannot reuse, need new cookies")
    return cookiejar, reuse
