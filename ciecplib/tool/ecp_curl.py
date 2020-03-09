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

"""Transfer a URL using SAML/ECP authentication.

This script attemps to use existing cookies for the target domain
and prompts for authorisation information if required.
Persistent cookies acquired during transactions are automatically
recorded in the cookie file, but session cookies are discarded (unless
--store-session-cookies is given).

Currently only HTTP GET requests are supported (patches welcome!).
"""

import sys

from .. import requests as ecp_requests
from ..cookies import load_cookiejar
from ..utils import DEFAULT_COOKIE_FILE
from .utils import (
    ArgumentParser,
    init_logging,
)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def create_parser():
    """Create a command-line argument parser

    Returns
    -------
    parser : `argparse.ArgumentParser`
    """
    parser = ArgumentParser(
        description=__doc__,
        prog="ecp-curl",
    )
    parser.add_argument(
        "url",
        help="the URL to transfer"
    )
    parser.add_argument(
        "-c",
        "--cookiefile",
        metavar="FILE",
        default=DEFAULT_COOKIE_FILE,
        help="cookie file to use",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="write debug output (uses both stderr and stdout)",
    )
    parser.add_identity_provider_argument()
    parser.add_argument(
        "-k",
        "--kerberos",
        action="store_true",
        default=False,
        help="enable kerberos negotiation"
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="write to %(metavar)s instead of stdout",
    )
    parser.add_argument(
        "-s",
        "--store-session-cookies",
        action="store_true",
        default=False,
        help="store session cookies in the cookie file"
    )
    parser.add_argument(
        "-u",
        "--username",
        help="authentication username, will be prompted for if not given "
             "and not using --kerberos"
    )
    return parser


def main(args=None):
    parser = create_parser()
    args = parser.parse_args(args=args)
    if args.debug:
        init_logging()
    cookiejar = load_cookiejar(
        args.cookiefile,
        strict=False,
    )
    if args.output:
        stream = open(args.output, "w")
    else:
        stream = sys.stdout
    try:
        print(
            ecp_requests.get(
                args.url,
                cookiefile=args.cookiefile,
                cookiejar=cookiejar,
                endpoint=args.identity_provider,
                username=args.username,
                kerberos=args.kerberos,
                store_cookies=args.store_session_cookies,
            ).text,
            file=stream,
            end="",
        )
    finally:
        if args.output:
            stream.close()


if __name__ == "__main__":
    main()
