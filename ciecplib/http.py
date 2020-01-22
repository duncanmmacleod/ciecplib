# -*- coding: utf-8 -*-
# Copyright (C) FNAL (2015-2016), Cardiff University (2019-2020)
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

"""HTTP methods for cigetcert
"""

import re
import socket
import warnings
try:
    from http import client as http_client
    from urllib import (
        request as urllib_request,
        parse as urllib_parse,
    )
    from urllib.error import HTTPError
except ImportError:  # python < 3
    import httplib as http_client
    import urllib2 as urllib_request
    import urlparse as urllib_parse
    URLError = urllib_request.HTTPError

try:
    import kerberos
except ImportError:  # windows
    import winkerberos as kerberos

from M2Crypto import (
    SSL,
    m2,
)

from .utils import (
    DEFAULT_CAFILE,
    DEFAULT_CAPATH,
)

__author__ = "Dave Dykstra, Duncan Macleod"


class _SslSocketWrapper(object):
    """Make a wrapper so a SSL Connection object can be opened as a file

    This is mostly from http://git.ganeti.org/?p=ganeti.git;a=commitdiff;h=beba56ae8;hp=70c815118f7f8bf151044cb09868d1e3d7a63ac8
    """  # noqa: E501
    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, name):
        # forward everything to underlying connection
        return getattr(self._conn, name)

    def makefile(self, mode, bufsize=0):
        try:
            return socket.SocketIO(self._conn, mode)
        except AttributeError:  # python < 3
            return socket._fileobject(self._conn, mode, bufsize)

    def close(self):
        # m2crypto always shuts down the SSL connection in the connection
        # close() function
        ret = self._conn.close()
        if (self._conn.get_shutdown() & 1) != 1:
            warnings.warn('close did not send shutdown')
        return ret


class CertValidatingHTTPSConnection(http_client.HTTPConnection):
    """Validate a certificate on an HTTPS connection with M2Crypto
    """
    default_port = http_client.HTTPS_PORT

    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 cert_chain_file=None, cafile=None, capath=None, **kwargs):
        http_client.HTTPConnection.__init__(self, host, port, **kwargs)
        self.host = host
        self.key_file = key_file
        self.cert_file = cert_file
        self.cert_chain_file = cert_chain_file
        self.cafile = cafile
        self.capath = capath

    def connect(self):
        # 'sslv23' actually means to accept all, then we turn off
        #   insecure sslv2 & sslv3
        context = SSL.Context('sslv23')
        # many websites say to disable SSL compression for CRIME attack
        #  but unfortunately m2crypto doesn't have a constant for it
        SSL_OP_NO_COMPRESSION = 0x00020000
        context.set_options(m2.SSL_OP_NO_SSLv2 |
                            m2.SSL_OP_NO_SSLv3 | SSL_OP_NO_COMPRESSION)
        # the example used for M2Crypto connections was mostly
        #   https://www.heikkitoivonen.net/blog/2008/10/14/ssl-in-python-26/
        if (self.cert_file is not None) or (self.key_file is not None):
            context.load_cert(self.cert_file, self.key_file)
        if self.cert_chain_file is not None:
            context.load_cert_chain(self.cert_chain_file)
        # Note that m2crypto does not verify CRLs.  There is an
        # extension package m2ext that does, but ignoring CRLs for the
        # well-managed servers that cigetcert connects to is deemed to
        # be an acceptable risk.
        context.set_verify(
            SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, depth=9)
        if context.load_verify_locations(self.cafile, self.capath) != 1:
            raise RuntimeError('Could not load verify locations ' +
                               str(self.cafile) + ' ' + str(self.capath))
        # The following cipher list is from "Disable weak ciphers" on
        # https://www.owasp.org/index.php/Transport_Layer_Protection_Cheat_Sheet
        # combined with the openssl man page at
        # https://www.openssl.org/docs/manmaster/apps/ciphers.html
        # You can see what remains by passing this list to
        #   openssl ciphers -v.
        if context.set_cipher_list('DEFAULT:!eNULL:!aNULL:!ADH:!EXP:!LOW:'
                                   '!MD5:!IDEA:!RC4:@STRENGTH') != 1:
            warnings.warn("no valid ciphers")
        sslconn = SSL.Connection(context)
        timeout = SSL.timeout(15)
        sslconn.set_socket_read_timeout(timeout)
        sslconn.set_socket_write_timeout(timeout)
        sslconn.connect((self.host, self.port))
        self.sock = _SslSocketWrapper(sslconn)


# -- handlers -----------------------------------------------------------------

class VerifiedHTTPSHandler(urllib_request.HTTPSHandler):
    def __init__(self, debuglevel=0, **kwargs):
        urllib_request.HTTPSHandler.__init__(self, debuglevel=debuglevel)
        self._connection_args = kwargs

    def http_class_wrapper(self, host, **kwargs):
        full_kwargs = dict(self._connection_args)
        full_kwargs.update(kwargs)
        return CertValidatingHTTPSConnection(host, **full_kwargs)

    def https_open(self, req):
        return self.do_open(self.http_class_wrapper, req)

    def http_error_401(self, request, response, code, msg, hdrs):
        return response


class NoRedirectHandler(urllib_request.HTTPRedirectHandler):
    def http_error_302(self, request, response, code, msg, hdrs):
        return response


class NoHttpHandler(urllib_request.HTTPHandler):
    def http_open(self, *args, **kwargs):
        raise ValueError('only https:// and file:// supported')


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
    rx = re.compile(r'(?:.*,)*\s*Negotiate\s*([^,]*),?', re.I)
    handler_order = 480  # before Digest auth

    def __init__(self, service_principal):
        """Create a new `HTTPNegotiateAuthHandler`
        """
        self.retried = 0
        self.context = None
        self.service_principal = service_principal

    def negotiate_value(self, headers):
        authreq = headers.get('www-authenticate', None)
        if authreq:
            mo = self.rx.search(authreq)
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
            self.service_principal,
        )
        if result < 1:
            return None

        if kerberos.authGSSClientStep(self.context, neg_value) < 0:
            return None
        return 'Negotiate {0}'.format(
            kerberos.authGSSClientResponse(self.context),
        )

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


# -- openers ------------------------------------------------------------------

def build_verified_opener(cookiejar=None, debug=False, cafile=DEFAULT_CAFILE,
                          capath=DEFAULT_CAPATH, redirect=False,
                          krb_endpoint=None):
    handlers = [
        urllib_request.HTTPCookieProcessor(cookiejar=cookiejar),
        VerifiedHTTPSHandler(cafile=cafile, capath=capath,
                             debuglevel=int(debug)),
        NoHttpHandler(),
    ]
    if not redirect:
        handlers.append(NoRedirectHandler())
    if krb_endpoint:
        loginhost = urllib_parse.urlparse(krb_endpoint).netloc.split(':')[0]
        handlers.append(
            HTTPNegotiateAuthHandler('HTTP@{0}'.format(loginhost))
        )
    return urllib_request.build_opener(*handlers)
