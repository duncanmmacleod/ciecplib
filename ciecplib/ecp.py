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

"""ECP authentication
"""

from __future__ import (print_function, absolute_import)

import base64
try:
    from urllib import (
        request as urllib_request,
        parse as urllib_parse,
    )
    from urllib.error import URLError
    from http.cookiejar import CookieJar
except ImportError:  # python < 3
    import urllib2 as urllib_request
    import urlparse as urllib_parse
    from cookielib import CookieJar
    URLError = urllib_request.URLError

from lxml import etree

from .http import build_verified_opener
from .utils import (
    DEFAULT_SP_URL,
    format_endpoint_url,
    prompt_username_password,
)

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


def get_xml_attribute(xdata, path, namespaces=None):
    if namespaces is None:
        namespaces = {
            'ecp': 'urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp',
            'S': 'http://schemas.xmlsoap.org/soap/envelope/',
            'paos': 'urn:liberty:paos:2003-08'
        }
    return xdata.xpath(path, namespaces=namespaces)[0]


def report_soap_fault(opener, url):
    soapfault = """
        <S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
           <S:Body>
             <S:Fault>
                <faultcode>S:Server</faultcode>
                <faultstring>responseConsumerURL from SP and assertionConsumerServiceURL from IdP do not match</faultstring>
             </S:Fault>
           </S:Body>
        </S:Envelope>"""  # noqa
    headers = {'Content-Type': 'application/vnd.paos+xml'}
    request = urllib_request.Request(url, headers=headers, data=soapfault)
    return opener.open(request)


def authenticate(
        endpoint,
        kerberos=False,
        spurl=DEFAULT_SP_URL,
        cookiejar=None,
        username=None,
        debug=False,
        **kwargs
):
    """Authenticate against an endpoint using ECP

    Parameters
    ----------
    endpoint : `str`
        the URL of the ECP endpoint to negotiate with

    kerberos : `bool`, or `str`, optional
        a `str` denoting the endpoint to use for kerberos negotiation,
        or `True` to use kerberos negotiation with the standard endpoint,
        otherwise do not use kerberos

    username : `str`, optional
        the username registered at the endpoint, if not given, and
        not using kerberos, this will be prompted for

    spurl : `str`, optional
        the URL of the service provider to authenticate against

    cookiejar : `http.cookiejar.CookieJar`, optional
        a cookie jar to store cookies in

    **kwargs
        other keyword arguments are passed to
        :func:`ligo.org.utils.build_verified_opener`

    Returns
    -------
    cookie : `http.cookiejar.Cookie`
        the newly created shibsession cookie
    cookiejar : `http.cookiejar.CookieJar`
        the cookiejar that contains the cookie(s)
    """
    endpoint = format_endpoint_url(endpoint)

    if kerberos is True:
        kerberos = endpoint

    # build HTTP request opener (if not given)
    if cookiejar is None:
        cookiejar = CookieJar()
    opener = build_verified_opener(
        cookiejar=cookiejar,
        krb_endpoint=kerberos,
        debug=debug,
        **kwargs
    )

    # -- step 1: initiate ECP request -----------

    # headers needed to indicate to the SP an ECP request
    headers = {
        'Accept': 'text/html; application/vnd.paos+xml',
        'PAOS': 'ver="urn:liberty:paos:2003-08";'
                '"urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"',
    }

    # request target from SP
    request = urllib_request.Request(
        url=spurl or endpoint,
        headers=headers,
    )
    response = opener.open(request)
    data = response.read()
    if debug:
        print("##### begin SP response\n")
        print(data.decode("utf-8"))
        print("\n##### end SP response")

    # convert the SP resonse from string to etree Element object
    spetree = etree.XML(data)

    # pick out the relay state element from the SP so that it can
    # be included later in the response to the SP
    relaystate = get_xml_attribute(
        spetree,
        "//ecp:RelayState",
    )
    rcurl = get_xml_attribute(
        spetree,
        "/S:Envelope/S:Header/paos:Request/@responseConsumerURL",
    )

    # remote the SOAP header to create a packge for the IdP
    idpbody = spetree
    idpbody.remove(idpbody[0])

    # -- step 2: authenticate with endpoint -----

    request = urllib_request.Request(
        endpoint,
        method='POST',
        data=etree.tostring(idpbody),
    )
    request.add_header('Content-Type', 'text/xml; charset=utf-8')

    # get credentials for non-kerberos request
    if not kerberos:
        # prompt the user for a password
        username, password = prompt_username_password(
            urllib_parse.urlparse(endpoint).netloc.split(':')[0],
            username=username,
        )
        # using the Authorization header
        pair = '%s:%s' % (username, password)
        try:
            base64string = base64.encodebytes(
                pair.encode('utf-8')).decode('utf-8')
        except AttributeError:  # python < 3
            base64string = base64.encodestring(pair)
        request.add_header('Authorization', 'Basic {0}'.format(
            base64string.replace('\n', '')))

    response = opener.open(request)
    data = response.read()

    if debug:
        print("##### begin IdP response")
        print(data.decode("utf-8"))
        print("##### end IdPesponse")

    # -- step 3: post back to the SP ------------

    try:
        idptree = etree.XML(data)
    except etree.XMLSyntaxError:
        raise RuntimeError(
            "Failed to parse response from {}, you most "
            "likely incorrectly entered your passphrase".format(
                endpoint,
            ),
        )
    acsurl = get_xml_attribute(
        idptree,
        "/S:Envelope/S:Header/ecp:Response/@AssertionConsumerServiceURL")

    # validate URLs between SP and IdP
    if acsurl != rcurl:
        try:
            report_soap_fault(opener, rcurl)
        except URLError:
            pass  # don't care, just doing a service

    # make a deep copy of the IdP response and replace its
    # header contents with the relay state initially sent by
    # the SP
    actree = idptree
    actree[0][0] = relaystate

    # POST the package to the SP
    headers = {'Content-Type': 'application/vnd.paos+xml'}
    request = urllib_request.Request(url=acsurl, method='POST',
                                     headers=headers,
                                     data=etree.tostring(actree))
    response = opener.open(request)

    # -- done -----------------------------------
    # we should now have an ECP cookie in the cookie jar

    cookie = cookiejar.make_cookies(response, request)[0]
    return cookie, cookiejar
