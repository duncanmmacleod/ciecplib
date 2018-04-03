# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2017)
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
import re
import getpass
import base64
import warnings
import time
from tempfile import gettempdir
from copy import deepcopy

from six.moves import http_cookiejar, input
from six.moves.urllib import (request as urllib_request)
from six.moves.urllib.parse import urlparse
from six.moves.urllib.error import HTTPError

from lxml import etree

import kerberos  # pykerberos module

from .kerberos import (klist, KerberosError)  # local kerberos utils

IDP_ENDPOINTS = {
    "LIGO.ORG": "https://login.ligo.org/idp/profile/SAML2/SOAP/ECP",
}

COOKIE_JAR = os.path.join(gettempdir(), 'ecpcookie.u%d' % os.getuid())


# -- authentication -----------------------------------------------------------

class HTTPNegotiateAuthHandler(urllib_request.BaseHandler):
    """Kerberos-based authentication handler

    This class uses an existing Kerberos ticket to authenticate
    via HTTP Negotiate Authentication. An instance of this class
    can be passed into the build_opener function from the urllib.request
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
            raise HTTPError(
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


# -- cookie jar ---------------------------------------------------------------

class ECPCookieJar(http_cookiejar.MozillaCookieJar):
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
                    cookie.domain, str(cookie.domain.startswith('.')).upper(),
                    cookie.path, str(cookie.secure).upper(), expires, name,
                    value]), file=f)


# -- requester ----------------------------------------------------------------

def request(url, endpoint=IDP_ENDPOINTS['LIGO.ORG'], use_kerberos=None,
            debug=False):
    """Request the given URL using ECP shibboleth authentication

    This requires an active Kerberos ticket for the user, to get one:

        >>> from ligo.org import kinit
        >>> kinit('albert.einstein')

    Then request as follows

        >>> from ligo.org import request
        >>> response = request(myurl)
        >>> print(response.read())

    Adapted from
    https://wiki.shibboleth.net/confluence/download/attachments/4358416/ecp.py

    Parameters
    ----------
    url : `str`
        URL path for request

    endpoint : `str`
        ECP endpoint URL for request

    use_kerberos : `bool`, optional
        use existing kerberos credential for login, default is to try, but
        fall back to username/password prompt

    debug : `bool`, optional, default: `False`
        query in verbose debugging mode

    Returns
    -------
    response : `str`
        the raw (decoded) response from the URL, probably XML/HTML or JSON
    """
    login_host = urlparse(endpoint).netloc

    # create a cookie jar and cookie handler (and read existing cookies)
    cookie_jar = ECPCookieJar()

    if os.path.exists(COOKIE_JAR):
        try:
            cookie_jar.load(COOKIE_JAR, ignore_discard=True)
        except http_cookiejar.LoadError as e:
            warnings.warn('Caught error loading ECP cookie: %s' % str(e))

    cookie_handler = urllib_request.HTTPCookieProcessor(cookie_jar)

    # need an instance of HTTPS handler to do HTTPS
    httpsHandler = urllib_request.HTTPSHandler(debuglevel = 0)
    if debug:
        httpsHandler.set_http_debuglevel(1)

    # create the base opener object
    opener = urllib_request.build_opener(cookie_handler, httpsHandler)

    # get kerberos credentials if available
    if use_kerberos is None:
        try:
            creds = klist()
        except KerberosError:
            use_kerberos = False
        else:
            if creds:
                use_kerberos = True
            else:
                use_kerberos = False
    if use_kerberos:
        opener.add_handler(HTTPNegotiateAuthHandler(
            service_principal='HTTP@%s' % login_host))

    # -- intiate ECP request --------------------

    # headers needed to indicate to the SP an ECP request
    headers = {
        'Accept': 'text/html; application/vnd.paos+xml',
        'PAOS': 'ver="urn:liberty:paos:2003-08";'
                '"urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"',
    }

    # request target from SP
    request = urllib_request.Request(url=url, headers=headers)
    response = opener.open(request)

    # convert the SP resonse from string to etree Element object
    sp_response = etree.XML(response.read())

    # pick out the relay state element from the SP so that it can
    # be included later in the response to the SP
    namespaces = {
        'ecp' : 'urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp',
        'S'   : 'http://schemas.xmlsoap.org/soap/envelope/',
        'paos': 'urn:liberty:paos:2003-08'
        }

    relay_state = sp_response.xpath("//ecp:RelayState",
                                    namespaces=namespaces)[0]

    # make a deep copy of the SP response and then remove the header
    # in order to create the package for the IdP
    idp_request = deepcopy(sp_response)
    header = idp_request[0]
    idp_request.remove(header)

    # -- authenticate with endpoint -------------

    request = urllib_request.Request(endpoint,
                                     data=etree.tostring(idp_request))
    request.get_method = lambda: 'POST'
    request.add_header('Content-Type', 'test/xml; charset=utf-8')

    # get credentials for non-kerberos request
    if not use_kerberos:
        # prompt the user for a password
        login = input("Enter username for %s: " % login_host)
        password = getpass.getpass("Enter password for login '%s': " % login)
        # combine the login and password, base64 encode, and send
        # using the Authorization header
        base64string = base64.encodestring(
            ('%s:%s' % (login, password)).encode()).decode().replace('\n', '')
        request.add_header('Authorization', 'Basic %s' % base64string)

    response = opener.open(request)
    idp_response = etree.XML(response.read())

    assertion_consumer_service = idp_response.xpath(
        "/S:Envelope/S:Header/ecp:Response/@AssertionConsumerServiceURL",
        namespaces=namespaces)[0]

    # make a deep copy of the IdP response and replace its
    # header contents with the relay state initially sent by
    # the SP
    sp_package = deepcopy(idp_response)
    sp_package[0][0] = relay_state

    headers = {'Content-Type' : 'application/vnd.paos+xml'}

    # POST the package to the SP
    request = urllib_request.Request(url=assertion_consumer_service,
                              data=etree.tostring(sp_package), headers=headers)
    request.get_method = lambda: 'POST'
    response = opener.open(request)

    # -- cache cookies --------------------------

    cookie_jar.save(COOKIE_JAR, ignore_discard=True)

    # -- actually send GET ----------------------

    myheaders = {'Accept': 'text/*'}    # allow any text mime not only html
    request = urllib_request.Request(url=url, headers=myheaders)
    response = opener.open(request)
    return response.read()
