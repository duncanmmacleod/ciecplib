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

    $ ecp-get-cookie -i 'My Institution' -u jsmith https://campus01.edu/my/secret/page

to authenticate with a password prompt, or

    $ ecp-get-cookie -i 'My Institution' -k https://campus01.edu/my/secret/page

to reuse an existing kerberos (``kinit``) credential.

By default the cookie file is created and stored in a location
defined by either

- ``/tmp/ecpcookie.u{uid}`` (Unix), or
- ``C:\Windows\Temp\ecpcookie.{username}`` (Windows)
"""  # noqa: E501

import argparse
import os
import sys

from ..cookies import (
    ECPCookieJar,
    has_session_cookies,
    load_cookiejar,
)
from ..ui import get_cookie
from ..utils import DEFAULT_COOKIE_FILE
from .utils import (
    ArgumentParser,
    init_logging,
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
        prog="ecp-get-cookie",
    )
    parser.add_argument(
        "target_url",
        metavar="URL",
        help="service URL for which to generate cookies",
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
    parser.add_argument(
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
        "-u",
        "--username",
        help="authentication username, will be prompted for if not given "
             "and not using --kerberos"
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


def parse_args(parser, args=None):
    """Parse and validate the command-line arguments

    Returns
    -------
    args : `argparse.Namespace`
    """
    args = parser.parse_args(args=args)

    if args.debug:
        args.verbose = True

    return args


def main(args=None):
    parser = create_parser()
    args = parse_args(parser, args=args)

    def vprint(*pargs, **kwargs):
        """Execute `print` only if --verbose was given
        """
        if args.verbose:
            print(*pargs, **kwargs)

    if args.debug:
        init_logging()

    # if asked to destroy, just do that
    if args.destroy:
        vprint("Removing cookie file {0!s}".format(args.cookiefile))
        os.unlink(args.cookiefile)
        sys.exit()

    # load old cookies (erroring if file is malformed only)
    try:
        cookiejar = load_cookiejar(args.cookiefile, strict=True)
    except FileNotFoundError:
        cookiejar = ECPCookieJar()

    # if we can't or won't reuse cookies, get a new one
    if not args.reuse or not has_session_cookies(
            cookiejar,
            args.target_url,
    ):
        vprint("Acquiring new session cookie...")
        cookie = get_cookie(
            args.target_url,
            endpoint=args.identity_provider,
            username=getattr(args, "username", None),
            cookiejar=None,
            cookiefile=None,
            kerberos=args.kerberos,
            debug=args.debug,
        )

        # write cookies back to the file
        vprint("Storing cookies...")

        cookiejar.set_cookie(cookie)
        cookiejar.save(
            args.cookiefile,
            ignore_discard=True,
            ignore_expires=True,
        )
        vprint("Cookie stored in '{0!s}'".format(args.cookiefile))
    else:
        vprint("Reusing existing cookies")

    # load the cert from file to print information
    if args.verbose:
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
