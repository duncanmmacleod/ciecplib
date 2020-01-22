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

import calendar
import datetime
import os
import math
import random
import string
import struct
import tempfile
import time
try:
    from urllib import parse as urllib_parse
    from urllib import request as urllib_request
except ImportError:  # python < 3
    import urlparse as urllib_parse
    import urllib2 as urllib_request

from OpenSSL import crypto

from M2Crypto import (X509, RSA, EVP, ASN1, m2)

from .ecp import (
    authenticate,
)
from .http import build_verified_opener

from .utils import (
    DEFAULT_SP_URL,
    format_endpoint_url,
)

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


# -- utilities ----------------------------------------------------------------

def _parse_unix_time(asn1time):
    return calendar.timegm(asn1time.get_datetime().timetuple())


def _random_string(length, outof=string.ascii_lowercase+string.digits):
    # http://stackoverflow.com/a/23728630/2213647 says SystemRandom()
    # is most secure
    return ''.join(random.SystemRandom().choice(outof) for _ in range(length))


# -- X.509 generator ----------------------------------------------------------

def get_x509_proxy_path():
    """Returns the default path for the X.509 certificate file

    Returns
    -------
    path : `str`
    """
    if os.getenv("X509_USER_PROXY"):
        return os.environ["X509_USER_PROXY"]
    if os.name == "nt":
        tmpdir = r'%SYSTEMROOT%\Temp'
        tmpname = "x509up_{0}".format(os.getlogin())
    else:
        tmpdir = "/tmp"
        tmpname = "x509up_u{0}".format(os.getuid())
    return os.path.join(tmpdir, tmpname)


def get_cert(
        endpoint,
        username=None,
        kerberos=False,
        hours=168,
        spurl=DEFAULT_SP_URL,
        debug=False,
):
    endpoint = format_endpoint_url(endpoint)

    # handle kerberos endpoint
    if kerberos is True:
        kerberos = endpoint

    # authenticate with IdP
    cookie, _ = authenticate(
        endpoint,
        username=username,
        kerberos=kerberos,
        debug=debug,
    )
    if debug:
        print("Authenticated against IdP with ECP")
        print("Requesting certificate from {0}".format(spurl))

    # request PKCS12 certificate from SP
    csrfstr = _random_string(10)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'CSRF={0}; {1.name}={1.value}'.format(csrfstr, cookie),
    }
    p12password = (
        _random_string(16, string.ascii_letters) +
        _random_string(2, string.digits) +
        _random_string(2, '!@#$%^&*()')
    )
    certdata = urllib_parse.urlencode({
        'submit': 'pkcs12',
        'CSRF': csrfstr,
        'p12password': p12password,
        'p12lifetime': math.ceil(hours),
    }).encode('utf-8')
    request = urllib_request.Request(
        url=spurl,
        headers=headers,
        data=certdata,
    )
    opener = build_verified_opener(debug=debug, krb_endpoint=kerberos)
    response = opener.open(request)

    if debug:
        print("Certificate received.")
    return crypto.load_pkcs12(
        response.read(),
        p12password.encode('utf-8'),
    )


# -- X.509 handling -----------------------------------------------------------

def load_cert(path, format=crypto.FILETYPE_PEM):
    """Load certificate from file

    Parameters
    ----------
    path : `str`
        the file path from which to read

    format : `int`, optional
        the format to read

    Returns
    -------
    cert : `OpenSSL.crypto.X509`
        the parsed certificate
    """
    with open(path, "r") as fobj:
        return crypto.load_certificate(
            format,
            fobj.read(),
        )


def _timeleft(cert):
    """Returns the number of seconds left on this certificate
    """
    try:  # M2Crypto
        expiry = cert.get_not_after().get_datetime().timetuple()
    except AttributeError:  # OpenSSL
        expiry = time.strptime(
            cert.get_notAfter().decode("utf-8"),
            "%Y%m%d%H%M%SZ",
        )
    return int(calendar.timegm(expiry) - time.time())


def _x509_name_str(obj):
    return "/" + "/".join([
        b"=".join(x).decode("utf-8") for x in obj.get_components()
    ])


def check_cert(cert, hours=1, proxy=None, rfc3820=True):
    """Validate an X509 certificate

    Parameters
    ----------
    cert : `OpenSSL.crypto.X509`
        the certificate object to check

    hours : `float`, optional
        minimum number of hours remaining before expiry

    proxy : `bool`, `NoneType`, optional
        if `True` (`False`), validate that the certificate is (is not)
        an impersonation proxy, if `None` (default) don't check.

    rfc3820 : `bool`, optional
        if `True` assert that, if the certificate is a proxy, that it
        is RFC 3820 compliant
    """
    # check expiry
    remaining = _timeleft(cert)
    if remaining < hours * 3600.:
        raise RuntimeError(
            "less than {0} hours remaining on X509 certificate".format(hours)
        )

    # check proxy type
    ctype = _cert_type(cert)
    isproxy = "proxy" in ctype
    if proxy is True and not isproxy:
        raise RuntimeError("certificate is not a proxy")
    if proxy is False and isproxy:
        raise RuntimeError("certificate is a proxy")
    if rfc3820 and "legacy globus proxy" in ctype:
        raise RuntimeError("proxy certificate is not RFC 3820 compliant")


def _cert_type(x509):
    # parse name entry as common name
    sub = x509.get_subject().get_components()
    if sub[-1][0] != b"CN":
        return "end entity credential"
    if sub[-1][1] == "proxy":
        return "full legacy globus proxy"
    if sub[-1][1] == "limited proxy":
        return "limited legacy globus proxy"

    # parse extensions for proxyCertInfo
    extensions = [x509.get_extension(i) for
                  i in range(x509.get_extension_count())]
    names = [e.get_short_name() for e in extensions]
    if b"proxyCertInfo" in names:
        return "RFC 3820 compliant impersonation proxy"
    return "end entity credential"


def print_cert_info(x509, path=None):
    """Print info about an X.509 certificate
    """
    pkey = x509.get_pubkey()
    print("subject  : " + _x509_name_str(x509.get_subject()))
    print("issuer   : " + _x509_name_str(x509.get_issuer()))
    print("type     : " + _cert_type(x509))
    print("strength : {0} bits".format(pkey.bits()))
    if path:
        print("path     : " + str(path))
    print("timeleft : " + str(datetime.timedelta(seconds=_timeleft(x509))))


def write_cert(path, pkcs12, use_proxy=False, minhours=168):
    """Write a PKCS12 certificate archive to file in X509 format

    Parameters
    ----------
    path : `str`
        the desired location of the final X509 file

    pkcs12 : `OpenSSL.crypto.PKCS12`
        a PKCS12 archive
    """
    certstr = crypto.dump_certificate(
        crypto.FILETYPE_PEM,
        pkcs12.get_certificate(),
    )
    keystr = crypto.dump_privatekey(
        crypto.FILETYPE_PEM,
        pkcs12.get_privatekey(),
    )
    if use_proxy:
        cert = X509.load_cert_string(certstr)
        key = EVP.load_key_string(keystr).get_rsa()
        proxy, proxykey = generate_proxy(cert, key, minhours=minhours)
        blocks = [proxy.as_pem(), proxykey.as_pem(cipher=None), certstr]
    else:
        blocks = [certstr, keystr]

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        # write cert and key to temporary location
        for block in blocks:
            tmp.write(block)
        tmp.close()

        # move tmpfile into place
        os.rename(tmp.name, path)


def generate_proxy(cert, key, minhours=168, limited=False, bits=2048):
    """Generate a proxy certificate based on a certificate

    Based on code from the gridproxy library
    https://github.com/abbot/gridproxy/blob/master/gridproxy/__init__.py
    which is Copyright Lev Shamardin and covered under the GNU GPLv3 license.

    Returns
    -------
    proxycert : `M2Crypto.X509.X509`
        the proxy certificate

    proxykey : `M2Crypto.EVP.PKey`
        the proxy private key
    """
    # according to
    #   https://en.wikipedia.org/wiki/RSA_%28cryptosystem%29#Key_generation
    # the exponent 65537 (2^16+1) is most efficient
    proxyrsa = RSA.gen_key(bits, 65537, lambda x: None)
    proxykey = EVP.PKey()
    proxykey.assign_rsa(proxyrsa)

    proxy = X509.X509()
    proxy.set_pubkey(proxykey)
    proxy.set_version(2)

    not_before = ASN1.ASN1_UTCTIME()
    not_before.set_time(_parse_unix_time(cert.get_not_before()))
    proxy.set_not_before(not_before)
    now = int(time.time())
    not_after = ASN1.ASN1_UTCTIME()
    not_after_time = now + int(minhours * 60 * 60)
    # make sure proxy doesn't expire later than the underlying cert
    cert_not_after_time = _parse_unix_time(cert.get_not_after())
    if not_after_time > cert_not_after_time:
        not_after_time = cert_not_after_time
    not_after.set_time(not_after_time)
    proxy.set_not_after(not_after)

    proxy.set_issuer_name(cert.get_subject())
    digest = EVP.MessageDigest('sha256')
    digest.update(proxykey.as_der())
    serial = struct.unpack("<L", digest.final()[:4])[0]
    proxy.set_serial_number(int(serial & 0x7fffffff))

    # It is not completely clear what happens with memory allocation
    # within the next calls, so after building the whole thing we are
    # going to reload it through der encoding/decoding.
    proxy_subject = X509.X509_Name()
    subject = cert.get_subject()
    for idx in range(subject.entry_count()):
        entry = subject[idx].x509_name_entry
        m2.x509_name_add_entry(proxy_subject._ptr(), entry, -1, 0)
    proxy_subject.add_entry_by_txt('CN', ASN1.MBSTRING_ASC,
                                   str(serial), -1, -1, 0)
    proxy.set_subject(proxy_subject)
    proxy.add_ext(X509.new_extension(
        "keyUsage", "Digital Signature, Key Encipherment, Data Encipherment",
        1))
    if limited:
        proxy.add_ext(X509.new_extension(
            "proxyCertInfo", "critical, language:1.3.6.1.4.1.3536.1.1.1.9", 1))
    else:
        proxy.add_ext(X509.new_extension(
            "proxyCertInfo", "critical, language:Inherit all", 1))

    sign_pkey = EVP.PKey()
    sign_pkey.assign_rsa(key, 0)
    proxy.sign(sign_pkey, 'sha256')

    return proxy, proxykey
