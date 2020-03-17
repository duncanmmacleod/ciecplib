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

import argparse
import logging
import os
import sys
from functools import wraps
from http.client import HTTPConnection

from .. import __version__
from ..cookies import (
    has_session_cookies,
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
        return super()._format_usage(
            usage,
            actions,
            groups,
            prefix,
        )


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        add_auth = kwargs.pop("add_auth", True)
        add_helpers = kwargs.pop("add_helpers", True)
        version = kwargs.pop("version", __version__)
        manpage = kwargs.pop("manpage", None)

        kwargs.setdefault("formatter_class", HelpFormatter)
        kwargs.setdefault("add_help", not add_helpers)
        super(ArgumentParser, self).__init__(*args, **kwargs)

        self._positionals.title = "Required arguments"
        if add_auth:
            self._optionals.title = "Other options"
        else:
            self._optionals.title = "Options"

        # add manpage options for argparse-manpage
        self._manpage = manpage

        # add auth options group
        if add_auth:
            self.add_auth_arguments()
            group = self._action_groups.pop(-1)
            self._action_groups.insert(1, group)

        # add helper commands group
        if add_helpers:
            self.add_helper_arguments(version=version)

    def add_helper_arguments(self, version=__version__):
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
        return helpers

    def add_auth_arguments(
            self,
            identity_provider=True,
            kerberos=True,
            username=True,
    ):
        auth = self.add_argument_group("Authentication options")

        if identity_provider:
            defaultidp = _get_default_idp()
            auth.add_argument(
                "-i",
                "--identity-provider",
                default=defaultidp,
                help="name of institution providing the identity (e.g. "
                     "'Cardiff University'), or domain name of IdP host "
                     "(e.g. idp.cf.ac.uk), see --list-idps for a list of "
                     "Identity Provider (IdPs) and their IdP URL. Shortened "
                     "institution names (e.g. 'Cardiff') can be given as "
                     "long as they uniquely match a full institution name "
                     "known by CILogon",
            )

        if kerberos:
            auth.add_argument(
                "-k",
                "--kerberos",
                action="store_true",
                default=False,
                help="enable kerberos negotiation",
            )

        if username:
            auth.add_argument(
                "-u",
                "--username",
                help="authentication username, will be prompted for if not "
                     "given and not using --kerberos",
            )

        return auth

    @wraps(argparse.ArgumentParser.parse_args)
    def parse_args(self, *args, **kwargs):
        args = super().parse_args(*args, **kwargs)
        # if -X/--destroy wasn't given and
        # -i/--identity-provider also wasn't given (and is supported)
        # then raise an error
        #    - this just supports giving -X/--destroy without having to
        #      also give -i/--identity-provider for no reason
        destroy = getattr(args, "destroy", None)
        idp = getattr(args, "identity_provider", False)
        if not destroy and idp is None:
            self.error(
                "the following arguments are required: -i/--identity-provider",
            )
        return args


class ListIdpsAction(argparse.Action):
    def __init__(
            self,
            option_strings,
            dest=argparse.SUPPRESS,
            default=argparse.SUPPRESS,
            help="show IdP names and URLs and exit",
    ):
        super().__init__(
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

def reuse_cookies(cookiejar, url, verbose=False):
    """Determine if a cookiejar has session cookies we can reuse

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
    reuse = has_session_cookies(cookiejar, url)
    if verbose and reuse:
        print("OK")
    elif verbose:
        print("cannot reuse, need new cookies")
    return cookiejar, reuse


def init_logging(level=logging.DEBUG):
    """Enable logging in requests.

    This function is taken from
    https://requests.readthedocs.io/en/v2.9.1/api/#api-changes
    """
    HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(level)
    requests_log = logging.getLogger("urllib3")
    requests_log.setLevel(level)
    requests_log.propagate = True
    return requests_log


def destroy_file(path, desc=None, verbose=False):
    """Destroy a file (if it exists), with verbose output
    """
    if verbose:
        desc = (desc or "").rstrip(" ") + " "
        print("Removing {}'{!s}'...".format(desc, path), end=" ")
    try:
        os.unlink(path)
    except FileNotFoundError:  # file doesn't exit, no matter
        if verbose:
            print("not found", end="")
    else:
        if verbose:
            print("done", end="")
    finally:
        if verbose:
            print()
