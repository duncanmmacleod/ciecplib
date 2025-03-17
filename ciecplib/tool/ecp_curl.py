# Copyright (C) 2019-2025 Cardiff University
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

ecp-curl attempts to use existing cookies for the target domain
and prompts for authorisation information if required.
Persistent cookies acquired during transactions are automatically
recorded in the cookie file, but session cookies are discarded (unless
--store-session-cookies is given).

Currently only HTTP GET requests are supported (patches welcome!).
"""

import sys
from email.parser import HeaderParser
from http.client import HTTPMessage

from ..cookies import load_cookiejar
from ..sessions import Session
from ..utils import DEFAULT_COOKIE_FILE
from .utils import (
    ArgumentParser,
)

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


def create_parser():
    """Create a command-line argument parser.

    Returns
    -------
    parser : `argparse.ArgumentParser`
    """
    parser = ArgumentParser(
        description=__doc__,
        prog="ecp-curl",
        add_auth=True,
        add_helpers=True,
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
    parser.add_argument(
        "-H",
        "--header",
        action="append",
        default=None,
        help="HTTP headers to include in the request",
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
    return parser


def format_headers(headers):
    """Format headers received on the command line.

    Each header should be formatted according to
    `RFC5322 <https://datatracker.ietf.org/doc/html/rfc5322.html#section-2.2>`_.

    Parameters
    ----------
    headers : `list` of `str`
        A list of header strings (``"Key: Value"``) to parse.

    Returns
    -------
    headerdict : `dict[str, str]`
        A `dict` of ``(key, value)`` headers ready to pass to `requests.get`.
    """
    if not headers:
        return {}
    headerstr = "\n".join(headers)
    return dict(HeaderParser(HTTPMessage).parsestr(headerstr))


def write(data, path):
    """Write ``data`` to a file path, or to stdout.

    Parameters
    ----------
    data : `bytes`
        The data to write.

    path : `str`, `None`
        The target path to write to, or `None` to write to stdout.
    """
    if path is None:
        file = sys.stdout.buffer
    else:
        file = open(path, "wb")
    try:
        file.write(data)
    finally:
        if path is not None:
            file.close()


def main(args=None):
    parser = create_parser()
    args = parser.parse_args(args=args)
    cookiejar = load_cookiejar(
        args.cookiefile,
        strict=False,
    )
    headers = format_headers(args.header)

    with Session(
        cookiejar=cookiejar,
        idp=args.identity_provider,
        username=args.username,
        kerberos=args.kerberos,
    ) as sess:
        # GET
        resp = sess.get(
            args.url,
            headers=headers,
        )
        resp.raise_for_status()
        # write
        write(resp.content, args.output)
        # store session cookies
        if args.store_session_cookies:
            sess.cookies.save(
                args.cookiefile,
                ignore_discard=True,
                ignore_expires=True,
            )


if __name__ == "__main__":
    main()
