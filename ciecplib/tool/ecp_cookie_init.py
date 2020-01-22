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

r"""Authenticate and store SAML/ECP session cookies.

There are two usages:

    $ ecp-cookie-init 'My Institution' https://campus01.edu/my/secret/page jsmith

to authenticate with a password prompt, or

    $ ecp-cookie-init 'My Institution' https://campus01.edu/my/secret/page

to reuse an existing kerberos (``kinit``) credential.

By default the cookie file is created and stored in a location
defined by either

- ``/tmp/ecpcookie.u{uid}`` (Unix), or
- ``C:\Windows\Temp\ecpcookie.{username}`` (Windows)
"""  # noqa: E501

from __future__ import print_function

import argparse
import os
import sys

from ..cookies import (
    COOKIE_FILE as DEFAULT_COOKIE_FILE,
    ECPCookieJar,
)
from ..ecp import authenticate
from .utils import (
    ArgumentParser,
    reuse_cookiefile,
)

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


def create_parser():
    """Create a command-line argument parser

    Returns
    -------
    parser : `argparse.ArgumentParser`
    """
    parser = ArgumentParser(
        description=__doc__,
        prog="ecp-cookie-init",
    )
    parser.add_argument(
        "target_url",
        metavar="URL",
        help="service URL for which to generate cookies",
    )
    authtype = parser.add_mutually_exclusive_group()
    authtype.add_argument(
        "username",
        nargs="?",
        default=argparse.SUPPRESS,
        help="authentication username, required if --kerberos not given",
    )

    parser.add_argument(
        "-c",
        "--cookiefile",
        metavar="cookiefile",
        default=DEFAULT_COOKIE_FILE,
        help="cookie file to create/reuse/destroy",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="write debug output to stdout (implies --verbose)",
    )
    parser.add_identity_provider_argument()
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
        help="reuse existing cookies if possible",
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
            args.kerberos or
            getattr(args, "username", None) and args.idp
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
            print("Removing cookie file {0!s}".format(args.cookiefile))
        os.unlink(args.cookiefile)
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
            args.identity_provider,
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
            print("Cookies stored in '{0!s}'".format(args.cookiefile))

    # load the cert from file to print information
    if args.debug or args.verbose:
        info = [(cookie.domain, cookie.path, cookie.secure, cookie.name) for
                cookie in cookiejar]
        fmt = "%-{0}s %-5s %-7s %s".format(max(len(i[0]) for i in info))
        print(fmt % ("------", "----", "-------", "----"))
        print(fmt % ("DOMAIN", "PATH", r"SECURE?", "NAME"))
        print(fmt % ("------", "----", "-------", "----"))
        for tup in info:
            print(fmt % tup)
        print(fmt % ("------", "----", "-------", "----"))


if __name__ == "__main__":
    main()
