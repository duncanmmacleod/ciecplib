# -*- coding: utf-8 -*-
# Copyright (C) Cardiff University (2019-2022)
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

r"""Authenticate and store session cookies.

ecp-get-cookie queries a SAML/ECP-enabled service, automatically performing
authentication where required, and saves cookies to use in future requests
to the same service.

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

import sys

from ..sessions import Session
from ..cookies import (
    ECPCookieJar,
    has_session_cookies,
    load_cookiejar,
)
from ..ui import get_cookie
from ..utils import DEFAULT_COOKIE_FILE
from .utils import (
    ArgumentParser,
    destroy_file,
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
        add_auth=True,
        add_helpers=True,
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


def parse_args(parser, args=None):
    """Parse and validate the command-line arguments

    Returns
    -------
    args : `argparse.Namespace`
    """
    # if user has given -X/--destroy, and isn't just asking for help
    # allow the URL positional argument to be empty
    sargs = set(sys.argv[1:] if args is None else args)
    if {"-X", "--destroy"} & sargs and not {"-h", "--help"} & sargs:
        parser._get_positional_actions()[0].nargs = "?"

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

    # if asked to destroy, just do that
    if args.destroy:
        destroy_file(args.cookiefile, "cookie file", verbose=args.verbose)
        return 0

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
        vprint("Initialising new session...")
        with Session(
            idp=args.identity_provider,
            cookiejar=cookiejar,
            username=getattr(args, "username", None),
            kerberos=args.kerberos,
        ) as sess:
            get_cookie(args.target_url, session=sess)

            # write cookies back to the file
            vprint("Storing cookies...")
            sess.cookies.save(
                args.cookiefile,
                ignore_discard=True,
                ignore_expires=True,
            )
        vprint("Cookie stored in '{0!s}'".format(args.cookiefile))
    else:
        vprint("Reusing existing cookies")

    # load the cert from file to print information
    if args.verbose:
        # reload cookies from the jar,
        # see https://github.com/duncanmmacleod/ciecplib/issues/109
        cookiejar = load_cookiejar(args.cookiefile, strict=True)
        # print information on each cookie
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
