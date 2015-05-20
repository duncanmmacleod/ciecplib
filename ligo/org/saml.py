# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2013)
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

"""This module provides LIGO.ORG authenticated HTML queries
"""

from __future__ import absolute_import

import os
import stat
import warnings
import tempfile
import getpass
import socket
import re

from six.moves.urllib import request as urllib2
from six.moves import http_cookiejar

import kerberos

from . import version

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Scott Koranda <scott.koranda@ligo.org>'
__version__ = version.version

COOKIE_JAR = os.path.join(tempfile.gettempdir(), getpass.getuser())
LIGO_LOGIN_URL = 'login.ligo.org'


class HTTPNegotiateAuthHandler(urllib2.BaseHandler):
    """Kerberos-based authentication handler

    This class uses an existing Kerberos ticket to authenticate
    via HTTP Negotiate Authentication. An instance of this class
    can be passed into the build_opener function from the urllib2
    module.

    Modified from source found at

    http://selenic.com/pipermail/mercurial/2008-June/019776.html

    Parameters
    ----------
    service_principal : `str`, optional
        the Kerberos principal of the authentication host
    """
    rx = re.compile('(?:.*,)*\s*Negotiate\s*([^,]*),?', re.I)
    handler_order = 480  # before Digest auth

    def __init__(self, service_principal='HTTP@login.ligo.org'):
        """Create a new `HTTPNegotiateAuthHandler`
        """
        self.retried = 0
        self.context = None
        self.service_principal = service_principal

    def negotiate_value(self, headers):
        authreq = headers.get('www-authenticate', None)
        if authreq:
            mo = HTTPNegotiateAuthHandler.rx.search(authreq)
            if mo:
                return mo.group(1)
        return None

    def generate_request_header(self, req, headers):
        neg_value = self.negotiate_value(headers)
        if neg_value is None:
            self.retried = 0
            return None

        if self.retried > 5:
            raise urllib2.HTTPError(
                req.get_full_url(), 401, "negotiate auth failed",
                headers, None)
        self.retried += 1

        result, self.context = kerberos.authGSSClientInit(
            self.service_principal)
        if result < 1:
            return None

        if kerberos.authGSSClientStep(self.context, neg_value) < 0:
            return None
        return 'Negotiate %s' % kerberos.authGSSClientResponse(self.context)

    def authenticate_server(self, headers):
        neg_value = self.negotiate_value(headers)
        if neg_value is None:
            return None
        elif kerberos.authGSSClientStep(self.context, neg_value) < 1:
            pass

    def clean_context(self):
        if self.context is not None:
            kerberos.authGSSClientClean(self.context)

    def http_error_401(self, req, fp, code, msg, headers):
        try:
            neg_hdr = self.generate_request_header(req, headers)

            if neg_hdr is None:
                return None

            req.add_unredirected_header('Authorization', neg_hdr)
            resp = self.parent.open(req)

            self.authenticate_server(resp.info())

            return resp

        finally:
            self.clean_context()


# -----------------------------------------------------------------------------
# Top-level request

def request(url, timeout=None, debug=False):
    """Request the given URL using LIGO.ORG SAML authentication.

    This requires an active Kerberos ticket for the user, to get one:

        >>> from ligo.org import kinit
        >>> kinit('albert.einstein')

    Then request as follows

        >>> from ligo.org import request
        >>> response = request(myurl)
        >>> print(response.read())

    Parameters
    ----------
    url : `str`
        URL path for request
    timeout : `int`, optional, default: no timeout
        number of seconds to wait for server response,
    debug : `bool`, optional, default: `False`
        Query in verbose debugging mode

    Returns
    -------
    response : `file`-like
        the raw response from the URL, probably XML/HTML or JSON

    Examples
    --------
    >>> from ligo.org import request
    >>> response = request('https://ldas-jobs.ligo.caltech.edu/')
    >>> print(response.read())
    """
    # set debug to 1 to see all HTTP(s) traffic
    debug = int(debug)

    # need an instance of HTTPS handler to do HTTPS
    httpshandler = urllib2.HTTPSHandler(debuglevel=debug)

    # use a cookie jar to store session cookies
    jar = http_cookiejar.LWPCookieJar()

    # if a cookie jar exists open it and read the cookies
    # and make sure it has the right permissions
    if os.path.exists(COOKIE_JAR):
        os.chmod(COOKIE_JAR, stat.S_IRUSR | stat.S_IWUSR)
        # set ignore_discard so that session cookies are preserved
        try:
            jar.load(COOKIE_JAR, ignore_discard=True)
        except http_cookiejar.LoadError as e:
            warnings.warn('http_cookiejar.LoadError caught: %s' % str(e))

    # create a cookie handler from the cookie jar
    cookiehandler = urllib2.HTTPCookieProcessor(jar)
    # need a redirect handler to follow redirects
    redirecthandler = urllib2.HTTPRedirectHandler()

    # need an auth handler that can do negotiation.
    # input parameter is the Kerberos service principal.
    auth_handler = HTTPNegotiateAuthHandler(
        service_principal='HTTP@%s' % LIGO_LOGIN_URL)

    # create the opener.
    opener = urllib2.build_opener(auth_handler, cookiehandler, httpshandler,
                                  redirecthandler)

    # prepare the request object
    req = urllib2.Request(url)

    # use the opener and the request object to make the request.
    if timeout is None:
        timeout = socket._GLOBAL_DEFAULT_TIMEOUT
    response = opener.open(req, timeout=timeout)

    # save the session cookies to a file so that they can
    # be used again without having to authenticate
    jar.save(COOKIE_JAR, ignore_discard=True)

    return response
