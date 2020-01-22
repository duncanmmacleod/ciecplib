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

r"""Print information about an existing X.509 credential.

"""  # noqa: E501

from __future__ import print_function

from ..x509 import (
    get_x509_proxy_path,
    load_cert,
    print_cert_info,
)
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
    )
    parser.add_argument(
        "-f",
        "--file",
        default=get_x509_proxy_path(),
        help="certificate file to create/reuse/destroy",
    )
    return parser


def parse_args(parser):
    """Parse and validate the command-line arguments

    Returns
    -------
    args : `argparse.Namespace`
    """
    return parser.parse_args()


def main():
    parser = create_parser()
    args = parse_args(parser)
    print_cert_info(load_cert(args.file), path=args.file)


if __name__ == "__main__":
    main()
