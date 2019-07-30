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

import argparse
import sys

from .. import (
    __version__,
    request,
)


__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def create_parser():
    """Create a command-line argument parser

    Returns
    -------
    parser : `argparse.ArgumentParser`
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "url",
        help="the URL to transfer"
    )
    parser.add_argument(
        "-c",
        "--cookie-jar",
        metavar="FILE",
        help="write cookies to %(metavar)s after operation",
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
        default="login.ligo.org",
        help="domain name of IdP host",
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
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=__version__,
        help="show version number and exit",
    )
    return parser


def main(args=None):
    parser = create_parser()
    args = parser.parse_args(args=args)
    if args.output:
        stream = open(args.output, "w")
    else:
        stream = sys.stdout
    try:
        print(
            request(
                args.url,
                cookiefile=args.cookie_jar,
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
