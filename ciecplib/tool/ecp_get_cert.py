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

"""Create an X.509 certificate using ECP authentication.

ecp-get-cert enables you to authenticate using SAML/ECP against any
identity provider registered with CILogon, and create an X.509
credential for use in querying services under the same identity and
access management domain.
"""

from ..ui import get_cert
from ..x509 import (
    check_cert,
    load_cert,
    print_cert_info,
    write_cert,
)
from ..utils import DEFAULT_X509_USER_FILE
from .utils import (
    ArgumentParser,
    destroy_file,
)

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"

EPILOG = r"""
Examples:

    $ ecp-get-cert -i 'My Institution'

to authenticate with a username and password prompt, or

    $ ecp-get-cert -u user.name -i 'My Institution'

to authenticate with only a password prompt, or

    $ ecp-get-cert -i 'My Institution' -k

to reuse an existing kerberos (``kinit``) credential.

The identitity provider name can be given in a number of ways, so long as the
argument uniquely identifies a provider.  For example, the following are all
equivalent:

    $ ecp-get-cert -i 'Cardiff University'
    $ ecp-get-cert -i Cardiff
    $ ecp-get-cert -i idp.cf.ac.uk
    $ ECP_IDP="Cardiff" ecp-get-cert

Environment:

X509_USER_PROXY:
    the default path for the credential file
ECP_IDP:
    the name/url of the default Identity Provider (--institution)
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
        prog="ecp-get-cert",
        manpage=MANPAGE,
        add_auth=True,
        add_helpers=True,
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="write debug output (uses both stderr and stdout, "
             "implies --verbose)",
    )
    parser.add_argument(
        "-f",
        "--file",
        default=DEFAULT_X509_USER_FILE,
        help="certificate file to create/reuse/destroy",
    )
    parser.add_argument(
        "-H",
        "--hours",
        type=int,
        default=277,
        help="lifetime of the certificate"
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
        help="destroy existing certificate"
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


def can_reuse(path, proxy=None):
    try:
        check_cert(load_cert(path), proxy=proxy)
    except (RuntimeError, OSError):
        return False
    return True


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
        destroy_file(args.file, "credential file", verbose=args.verbose)
        return 0

    # if asked to reuse, check that we can
    if args.reuse:
        vprint("Validating existing certificate...", end=" ")
        args.reuse = can_reuse(args.file, proxy=args.proxy)
        if args.reuse:
            vprint("OK")
        else:
            vprint("failed, will regenerate")

    # get new certificate
    if not args.reuse:
        vprint("Fetching certificate...")
        cert, key = get_cert(
            endpoint=args.identity_provider,
            username=getattr(args, "username", None),
            kerberos=args.kerberos,
            hours=args.hours,
            debug=args.debug,
        )

        # write certificate to a file
        vprint("Storing certificate...")
        write_cert(
            args.file,
            cert,
            key,
            use_proxy=args.proxy,
            minhours=args.hours,
        )
        vprint("X.509 credential stored")

    # load the cert from file to print information
    if args.verbose:
        print_cert_info(
            load_cert(args.file),
            path=args.file,
            verbose=True,
        )


if __name__ == "__main__":
    main()
