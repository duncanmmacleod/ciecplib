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

"""Transfer a URL using LIGO.ORG SAML/ECP authentication
"""

from __future__ import print_function

import sys

from .. import (
    __version__,
    request,
)
from ..cookies import COOKIE_FILE as DEFAULT_COOKIE_FILE
from ..ecp import LIGO_ENDPOINT_DOMAIN
from .utils import (
    ArgumentParser,
    reuse_cookiefile,
)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def create_parser():
    """Create a command-line argument parser

    Returns
    -------
    parser : `argparse.ArgumentParser`
    """
    parser = ArgumentParser(description=__doc__, version=__version__)
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
        help="write debug output to stdout (implies --verbose)",
    )
    parser.add_argument(
        "-i",
        "--hostname",
        default=LIGO_ENDPOINT_DOMAIN,
        help="domain name of IdP host, see --list-idps for a list of"
             "Identity Provider (IdPs) and their IdP endpoint URL",
    )
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
        "-u",
        "--username",
        help="username on IdP host, will be prompted for if not given "
             "and not using --kerberos"
    )
    return parser


def main(args=None):
    parser = create_parser()
    args = parser.parse_args(args=args)
    if args.output:
        stream = open(args.output, "w")
    else:
        stream = sys.stdout
    cookiejar = reuse_cookiefile(
        args.cookiefile,
        args.url,
        verbose=False,
    )[0]
    try:
        print(
            request(
                args.url,
                cookiefile=args.cookiefile,
                cookiejar=cookiejar,
                endpoint=args.hostname,
                debug=args.debug,
                username=args.username,
                kerberos=args.kerberos,
            ).read().decode("utf-8"),
            file=stream,
            end="",
        )
    finally:
        if args.output:
            stream.close()


if __name__ == "__main__":
    main()
