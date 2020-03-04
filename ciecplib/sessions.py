# -*- coding: utf-8 -*-
# Copyright (C) Cardiff University (2020)
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

"""ECP-integated requests session
"""

from functools import wraps

from requests_ecp import Session as ECPSession

from .cookies import ECPCookieJar
from .env import _get_default_idp
from .kerberos import has_credential
from .utils import (
    DEFAULT_COOKIE_FILE,
    format_endpoint_url,
)

__all__ = [
    "Session",
]


class Session(ECPSession):
    """`requests.Session` with default ECP auth and pre-populated cookies
    """
    def __init__(
            self,
            idp=_get_default_idp(),
            kerberos=None,
            username=None,
            password=None,
            cookiejar=None,
            cookiefile=DEFAULT_COOKIE_FILE,
            store_cookies=False,
    ):
        from .cookies import (
            ECPCookieJar,
            load_cookiejar,
        )

        if kerberos is None:
            kerberos = has_credential()

        # open session with ECP authentication
        super(Session, self).__init__(
            idp=format_endpoint_url(idp),
            kerberos=kerberos,
            username=username,
            password=password,
        )

        # load cookies from existing jar or file
        self._cookiefile = cookiefile if store_cookies else None
        self.cookies = ECPCookieJar()
        if cookiejar is None and cookiefile is not None:
            cookiejar = load_cookiejar(cookiefile, strict=False)
        if cookiejar is not None:
            self.cookies.update(cookiejar)

    @wraps(ECPSession.close)
    def close(self):
        super(Session, self).close()

        # cache cookies for next time (only if using our fancy jar)
        if self._cookiefile and isinstance(self.cookies, ECPCookieJar):
            self.cookies.save(
                self._cookiefile,
                ignore_discard=True,
                ignore_expires=True,
            )
