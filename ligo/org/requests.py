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

from __future__ import (print_function, absolute_import)

try:
    from urllib.request import Request
except ImportError:  # python < 3
    from urllib2 import Request

from .cookies import (
    COOKIE_FILE,
    ECPCookieJar,
    has_session_cookies,
    load_cookiejar,
)
from .ecp import (LIGO_ENDPOINT_DOMAIN, authenticate)
from .http import build_verified_opener
from .kerberos import has_credential
from .utils import format_endpoint_url


def request(
        url,
        username=None,
        endpoint=LIGO_ENDPOINT_DOMAIN,
        kerberos=None,
        cookiejar=None,
        cookiefile=COOKIE_FILE,
        debug=False,
        store_session_cookies=False,
):
    """Request the given URL using ECP shibboleth authentication

        >>> from ligo.org import request
        >>> response = request(myurl)
        >>> print(response.read())

    Parameters
    ----------
    url : `str`
        URL path for request

    endpoint : `str`, optional
        ECP endpoint URL for request

    kerberos : `bool`, optional
        use existing kerberos credential for login, default is to try, but
        fall back to username/password prompt

    debug : `bool`, optional, default: `False`
        query in verbose debugging mode

    Returns
    -------
    response : `http.client.HTTPResponse`
        the response from the URL
    """
    endpoint = format_endpoint_url(endpoint, kerberos=kerberos)

    # read existing cookies
    if cookiejar is None:
        cookiejar = load_cookiejar(cookiefile, strict=False)
    reuse = has_session_cookies(cookiejar, url)

    # -- authenticate ---------------------------

    if not reuse:
        if kerberos is None:  # guess availability of kerberos
            kerberos = has_credential()
        authenticate(
            endpoint,
            username=username,
            spurl=url,
            kerberos=kerberos,
            cookiejar=cookiejar,
            debug=debug,
        )

        # cache cookies for next time (only if using our fancy jar)
        if isinstance(cookiejar, ECPCookieJar) and cookiefile is not None:
            cookiejar.save(
                cookiefile,
                ignore_discard=store_session_cookies,
                ignore_expires=store_session_cookies,
            )

    # -- actually send GET ----------------------

    myheaders = {'Accept': 'text/*'}    # allow any text mime not only html
    request = Request(url=url, headers=myheaders)
    opener = build_verified_opener(cookiejar=cookiejar, debug=debug)
    response = opener.open(request)
    return response
