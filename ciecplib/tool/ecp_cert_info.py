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

"""Print information about an existing X.509 credential.

ecp-cert-info prints information from an existing X.509 credential,
including owner information, certificate type, and time remaining
until expiry.
"""

from datetime import timedelta

from ..x509 import (
    load_cert,
    print_cert_info,
    time_left,
)
from ..utils import DEFAULT_X509_USER_FILE
from .utils import (
    ArgumentParser,
)

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"

EPILOG = r"""
Environment:

X509_USER_PROXY:
    the default path for the credential file
"""

MANPAGE = [
    {'heading': 'environment',
     'content': """
.TP
.B "X509_USER_PROXY"
The default path for the credential file """,
     },
]


def _hours_minutes(argstring):
    """Parse the --valid argument as hours:minutes

    Returns the argument as a float in seconds
    """
    try:
        hrs, minutes = argstring.split(":")
    except TypeError as exc:
        exc.args = ("--valid argument must be in the format H:M",)
        raise
    return float(hrs) * 3600. + float(minutes) * 60.


def create_parser():
    """Create a command-line argument parser

    Returns
    -------
    parser : `argparse.ArgumentParser`
    """
    parser = ArgumentParser(
        description=__doc__,
        epilog=EPILOG,
        manpage=MANPAGE,
        prog="ecp-cert-info",
        add_auth=False,
        add_helpers=True,
    )
    parser.add_argument(
        "-f",
        "--file",
        default=DEFAULT_X509_USER_FILE,
        help="certificate file to read (must exist)",
    )
    parser.add_argument(
        "-v",
        "--valid",
        type=_hours_minutes,
        help="time requirement for proxy to be valid",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="print full text of certificate",
    )
    return parser


def parse_args(parser, args=None):
    """Parse and validate the command-line arguments

    Returns
    -------
    args : `argparse.Namespace`
    """
    return parser.parse_args(args=args)


def main(args=None):
    parser = create_parser()
    args = parse_args(parser, args=args)

    # load certificate
    cert = load_cert(args.file)

    # print certificate information
    print_cert_info(
        cert,
        path=args.file,
        verbose=args.verbose,
    )

    # assert --valid if given
    if args.valid:
        assert time_left(cert) >= args.valid, (
            "timeleft is less than required {}".format(
                timedelta(seconds=args.valid),
            )
        )


if __name__ == "__main__":
    main()
