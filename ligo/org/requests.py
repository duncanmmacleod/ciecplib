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

import os
import warnings
import time
from pathlib import Path
from tempfile import gettempdir
try:
    from http.cookiejar import (LoadError, MozillaCookieJar)
    from urllib.parse import urlparse
    from urllib.request import Request
except ImportError:  # python < 3
    from cookielib import (LoadError, MozillaCookieJar)
    from urllib2 import Request
    from urlparse import urlparse

from .ecp import authenticate
from .http import build_verified_opener
from .kerberos import has_credential
from .utils import get_idp_urls

LIGO_ECP_ENDPOINT = "login.ligo.org"
try:
    COOKIE_FILE = Path(gettempdir()) / 'ecpcookie.u{}'.format(os.getuid())
except AttributeError:  # no os.getuid means windows
    COOKIE_FILE = Path(gettempdir()) / 'ecpcookie.{}'.format(os.getlogin())


def _get_endpoint_url(institution, kerberos=False):
    return get_idp_urls(institution)[int(kerberos)]


# -- cookie jar ---------------------------------------------------------------

class ECPCookieJar(MozillaCookieJar):
    """Custom cookie jar

    Adapted from
    https://wiki.shibboleth.net/confluence/download/attachments/4358416/ecp.py
    """
    def save(self, filename=None, ignore_discard=False, ignore_expires=False):
        with open(filename, 'w') as f:
            f.write(self.header)
            for cookie in self:
                if not ignore_discard and cookie.discard:
                    continue
                if not ignore_expires and cookie.is_expired(time.time()):
                    continue
                if cookie.expires is not None:
                    expires = str(cookie.expires)
                else:
                    # change so that if a cookie does not have an expiration
                    # date set it is saved with a '0' in that field instead
                    # of a blank space so that the curl libraries can
                    # read in and use the cookie
                    expires = "0"
                if cookie.value is None:
                    # cookies.txt regards 'Set-Cookie: foo' as a cookie
                    # with no name, whereas cookiejar regards it as a
                    # cookie with no value.
                    name = ""
                    value = cookie.name
                else:
                    name = cookie.name
                    value = cookie.value
                print('\t'.join([
                    cookie.domain,
                    str(cookie.domain.startswith('.')).upper(),
                    cookie.path,
                    str(cookie.secure).upper(),
                    expires,
                    name,
                    value,
                ]), file=f)


def request(
        url,
        username=None,
        endpoint=LIGO_ECP_ENDPOINT,
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
    if endpoint is None:
        endpoint = _get_endpoint_url("LIGO.*")

    # -- initialise URL opener ------------------

    # create a cookie jar and cookie handler (and read existing cookies)
    if cookiejar is None:
        cookiejar = ECPCookieJar()
        if Path(cookiefile or '').is_file():
            try:
                cookiejar.load(
                    cookiefile,
                    ignore_discard=True,
                )
            except LoadError as e:
                warnings.warn('Caught error loading ECP cookie: %s' % str(e))

    for cookie in cookiejar:
        if (
                cookie.name.startswith("_shibsession_") and
                cookie.domain == urlparse(url).netloc and
                cookie.expires is None
        ):
            reuse = True
            break
    else:
        reuse = False

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
            )

    # -- actually send GET ----------------------

    myheaders = {'Accept': 'text/*'}    # allow any text mime not only html
    request = Request(url=url, headers=myheaders)
    opener = build_verified_opener(cookiejar=cookiejar, debug=debug)
    response = opener.open(request)
    return response
