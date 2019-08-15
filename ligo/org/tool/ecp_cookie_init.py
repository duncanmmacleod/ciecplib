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

r"""Authenticate and store SAML/ECP session cookies.

There are two usages:

1) ``ecp-cookie-init Campus01 https://campus01.edu/my/secret/page jsmith``

to authenticate with a password prompt, or

2) ``ecp-cookie-init -k https://campus01.edu/my/secret/page``

to reuse an existing kerberos (``kinit``) credential.
By default the cookie file is created and stored in a location
defined by either

- ``/tmp/ecpcookie.u{uid}`` (Unix), or
- ``C:\Windows\Temp\ecpcookie.{username}`` (Windows)
"""

from __future__ import print_function

import argparse
import sys
from pathlib import Path

from .. import __version__
from ..cookies import (
    COOKIE_FILE as DEFAULT_COOKIE_FILE,
    ECPCookieJar,
)
from ..ecp import authenticate
from .utils import (
    ArgumentParser,
    reuse_cookiefile,
)


def create_parser():
    """Create a command-line argument parser

    Returns
    -------
    parser : `argparse.ArgumentParser`
    """
    parser = ArgumentParser(description=__doc__, version=__version__)
    parser.add_argument(
        "endpoint",
        metavar="IdP",
        nargs="?",
        default=argparse.SUPPRESS,
        help="IdP name, e.g. 'LIGO.ORG', or the URL of an IdP endpoint, "
             "required if --kerberos not given, see --list-idps for a list of"
             "Identity Provider (IdPs) and their IdP endpoint URL"
    )
    parser.add_argument(
        "target_url",
        metavar="URL",
        help="service URL for which to generate cookies",
    )
    authtype = parser.add_mutually_exclusive_group()
    authtype.add_argument(
        "username",
        metavar="login",
        nargs="?",
        default=argparse.SUPPRESS,
        help="identity username, required if --kerberos not given",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="write debug output to stdout (implies --verbose)",
    )
    parser.add_argument(
        "-c",
        "--cookiefile",
        metavar="cookiefile",
        default=DEFAULT_COOKIE_FILE,
        type=Path,
        help="cookie file to create/reuse/destroy",
    )
    parser.add_argument(
        "-i",
        "--hostname",
        default=argparse.SUPPRESS,
        help="domain name of IdP host, defaults is default domain for IdP",
    )
    authtype.add_argument(
        "-k",
        "--kerberos",
        action="store_true",
        default=False,
        help="enable kerberos negotiation, required if username not given"
    )
    parser.add_argument(
        "-r",
        "--reuse",
        default=False,
        action="store_true",
        help="reuse an existing cookies if possible",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="write verbose output to stdout",
    )
    parser.add_argument(
        "-X",
        "--destroy",
        action="store_true",
        default=False,
        help="destroy existing cookie file"
    )
    return parser


def parse_args(parser):
    """Parse and validate the command-line arguments

    Returns
    -------
    args : `argparse.Namespace`
    """
    args = parser.parse_args()

    # check that username or --kerberos was given if not using --destroy
    if not args.destroy and not (
            args.kerberos or getattr(args, "username", None) and args.endpoint
    ):
        parser.error("-k/--kerberos is required if IdP_tag and "
                     "login are not given")

    if args.debug:
        args.verbose = True

    return args


def main():
    parser = create_parser()
    args = parse_args(parser)

    # if asked to destroy, just do that
    if args.destroy:
        if args.verbose:
            print("Removing cookie file {!s}".format(args.cookiefile))
        args.cookiefile.unlink()
        sys.exit()

    # if asked to reuse, check that we can
    cookiejar = None
    if args.reuse:
        cookiejar, args.reuse = reuse_cookiefile(
            args.cookiefile,
            args.target_url,
            verbose=args.verbose,
        )

    # get new certificate
    if not args.reuse:
        cookiejar = cookiejar or ECPCookieJar()
        if args.verbose:
            print("Authenticating...")
        authenticate(
            getattr(args, "hostname", None) or args.endpoint,
            spurl=args.target_url,
            cookiejar=cookiejar,
            username=getattr(args, "username", None),
            kerberos=args.kerberos,
            debug=args.debug,
        )

        # write certificate to a file
        if args.verbose:
            print("Storing cookies...")
        cookiejar.save(
            args.cookiefile,
            ignore_discard=True,
            ignore_expires=True,
        )
        if args.verbose:
            print("Cookies stored in '{!s}'".format(args.cookiefile))

    # load the cert from file to print information
    if args.debug or args.verbose:
        info = [(cookie.domain, cookie.path, cookie.secure, cookie.name) for
                cookie in cookiejar]
        fmt = "%-{}s %-5s %-7s %s".format(max(len(i[0]) for i in info))
        print(fmt % ("------", "----", "-------", "----"))
        print(fmt % ("DOMAIN", "PATH", r"SECURE?", "NAME"))
        print(fmt % ("------", "----", "-------", "----"))
        for tup in info:
            print(fmt % tup)
        print(fmt % ("------", "----", "-------", "----"))


if __name__ == "__main__":
    main()
