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

r"""Create a LIGO.ORG X.509 certificate.

There are two usages:

1) ``ligo-proxy-init albert.einstein``

to authenticate with a password prompt, or

2) ``ligo-proxy-init -k``

to reuse an existing kerberos (``kinit``) credential.
By default the credential file is created and stored in a location
defined by either

- ``${X509_USER_PROXY}`` or ``/tmp/x509up_u{uid}`` (Unix)
- ``%X509_USER_PROXY%`` or ``C:\Windows\Temp\x509up_{username}`` (Windows),
"""

from __future__ import print_function

import argparse
import os
import sys
from distutils.spawn import find_executable
from pathlib import Path

from OpenSSL import crypto

from ..x509 import (
    check_cert,
    get_cert,
    load_cert,
    print_cert_info,
    write_cert,
)

__version__ = "0.1.0"


class HelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    pass


def get_x509_proxy_path():
    """Returns the default path for the X.509 certificate file

    Returns
    -------
    path : `pathlib.Path`
    """
    if os.getenv("X509_USER_PROXY"):
        return Path(os.environ["X509_USER_PROXY"])
    if os.name == "nt":
        tmpdir = Path(r'%SYSTEMROOT%\Temp')
        tmpname = "x509up_{}".format(os.getlogin())
    else:
        tmpdir = Path("/tmp")
        tmpname = "x509up_u{}".format(os.getuid())
    return tmpdir / tmpname


def find_cigetcert(name="cigetcert"):
    """Returns the path of the cigetcert executable

    If cigetcert isn't on the path, this function presumes that it
    lives in the same directory as this script, which it will when
    bundled.

    Returns
    -------
    path : `pathlib.Path`
    """
    print(__file__)
    return Path(find_executable(name)) or str(
        Path(__file__).parent.absolute() / name
    )


def find_ca_certificates_file():
    """Returns the location of ``cacert.pem`` provided by ca-certificates

    Returns
    -------
    path : `pathlib.Path`
    """
    prefix = Path(sys.prefix)
    if os.name == "nt":
        sslpath = prefix / "Library" / "ssl"
    else:
        sslpath = prefix / "ssl"
    return sslpath / "cacert.pem"


def create_parser():
    """Create a command-line argument parser

    Returns
    -------
    parser : `argparse.ArgumentParser`
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=HelpFormatter,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=__version__,
        help="show version information and exit"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="write verbose output to stdout",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="write debug output to stdout (implies --verbose)",
    )
    method = parser.add_mutually_exclusive_group()
    method.add_argument(
        "username",
        nargs="?",
        default=argparse.SUPPRESS,
        help="LIGO.ORG (albert.einstein) username, "
             "required if --kerberos not given",
    )
    method.add_argument(
        "-k",
        "--kerberos",
        action="store_true",
        default=False,
        help="enable kerberos negotiation, required if username not given"
    )
    parser.add_argument(
        "-i",
        "--hostname",
        default="login.ligo.org",
        help="domain name of IdP host",
    )
    parser.add_argument(
        "-H",
        "--hours",
        type=int,
        default=277,
        help="lifetime of the certificate"
    )
    parser.add_argument(
        "-f",
        "--file",
        default=get_x509_proxy_path(),
        type=Path,
        help="certificate file to create/reuse/destroy",
    )
    parser.add_argument(
        "-p",
        "--proxy",
        action="store_true",
        default=False,
        help="create RFC 3820 compliant impersonation proxy"
    )
    parser.add_argument(
        "-r",
        "--reuse",
        default=False,
        type=float,
        const=1.,
        nargs="?",
        metavar="HOURS",
        help="reuse an existing certificate if valid for more than "
             "%(const)s hours, or pass a number of hours to specify",
    )
    parser.add_argument(
        "-X",
        "--destroy",
        action="store_true",
        default=False,
        help="destroy existing certificate"
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
            getattr(args, "username", None) or args.kerberos
    ):
        parser.error("one of username or -k/--kerberos is required")

    if getattr(args, "username", None):
        args.username = args.username.split('@')[0]

    if args.debug:
        args.verbose = True

    return args


def can_reuse(path, proxy=None):
    try:
        check_cert(load_cert(path), proxy=proxy)
    except (RuntimeError, OSError):
        return False
    return True


def main():
    parser = create_parser()
    args = parse_args(parser)

    # if asked to destroy, just do that
    if args.destroy:
        if args.verbose:
            print("Removing credential file {!s}".format(args.file))
        args.file.unlink()
        sys.exit()

    # if asked to reuse, check that we can
    if args.reuse:
        if args.verbose:
            print("Validating existing certificate...", end=" ")
        args.reuse = can_reuse(args.file, proxy=args.proxy)
        if args.verbose and args.reuse:
            print("OK")
        elif args.verbose:
            print("failed, will regenerate")

    # get new certificate
    if not args.reuse:
        if args.verbose:
            print("Fetching certificate...")
        cert = get_cert(
            args.hostname,
            username=getattr(args, "username", None),
            kerberos=args.kerberos,
            hours=args.hours,
            debug=args.debug,
        )

        # write certificate to a file
        if args.verbose:
            print("Storing certificate...")
        write_cert(
            args.file,
            cert,
            use_proxy=args.proxy,
            minhours=args.hours,
        )
        if args.verbose:
            print("X.509 credential stored")

    # load the cert from file to print information
    if args.debug or args.verbose:
        x509 = load_cert(args.file)

    # dump full text of cert
    if args.debug:
        certstr = crypto.dump_certificate(
            crypto.FILETYPE_PEM,
            x509,
        )
        print(certstr.decode("utf-8"), end="")

    # print certificate/proxy info
    if args.verbose:
        print_cert_info(x509, path=args.file)


if __name__ == "__main__":
    main()
