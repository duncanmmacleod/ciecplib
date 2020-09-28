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

from requests_ecp import Session as ECPSession

from .cookies import ECPCookieJar
from .env import _get_default_idp
from .kerberos import has_credential
from .utils import get_idp_url

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
    ):

        if kerberos is None:
            kerberos = has_credential()

        # open session with ECP authentication
        super().__init__(
            idp=get_idp_url(idp),
            kerberos=kerberos,
            username=username,
            password=password,
        )

        # load cookies from existing jar or file
        self.cookies = ECPCookieJar()
        if cookiejar:
            self.cookies.update(cookiejar)
