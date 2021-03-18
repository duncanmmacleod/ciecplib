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
import shutil
import struct
import sys
import tempfile
import time

from OpenSSL import crypto

from M2Crypto import (X509, RSA, EVP, ASN1, m2)

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


def _parse_unix_time(asn1time):
    """Parse an ASN1 unix time into a python `time` tuple
    """
    return calendar.timegm(asn1time.get_datetime().timetuple())


def load_cert(path, format=crypto.FILETYPE_PEM):
    """Load certificate from file

    Parameters
    ----------
    path : `str`, `pathlib.Path`
        the file path from which to read

    format : `int`, optional
        the format to read

    Returns
    -------
    cert : `OpenSSL.crypto.X509`
        the parsed certificate
    """
    with open(str(path), "r") as fobj:
        return crypto.load_certificate(
            format,
            fobj.read(),
        )


def time_left(cert):
    """Returns the number of seconds left on this certificate

    If the certificate has expired, ``0`` is returned.
    """
    try:  # M2Crypto
        expiry = cert.get_not_after().get_datetime().timetuple()
    except AttributeError:  # OpenSSL
        expiry = time.strptime(
            cert.get_notAfter().decode("utf-8"),
            "%Y%m%d%H%M%SZ",
        )
    return max(0, int(calendar.timegm(expiry) - time.time()))


def _x509_name_str(obj):
    """Return the name of the x509 object as a string
    """
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

    proxy : `bool`, `None`, optional
        if `True` (`False`), validate that the certificate is (is not)
        an impersonation proxy, if `None` (default) don't check.

    rfc3820 : `bool`, optional
        if `True` assert that, if the certificate is a proxy, that it
        is RFC 3820 compliant
    """
    # check expiry
    remaining = time_left(cert)
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
    """Returns the type of the given x509 certificate object
    """
    # convert openssl to m2crypto for convenience
    if isinstance(x509, crypto.X509):
        x509 = X509.load_cert_string(crypto.dump_certificate(
            crypto.FILETYPE_PEM,
            x509,
        ))
    # parse name entry as common name
    sub = x509.get_subject()
    ntype, name = str(sub).split("/")[-1].split('=', 1)

    # if name entry is not 'common name' then EEC
    if ntype != "CN":
        return "end entity credential"

    if name == "proxy":
        return "full legacy globus proxy"
    if name == "limited proxy":
        return "limited legacy globus proxy"

    # get policy language
    try:
        policy = _get_cert_policy_language(x509)
    except ValueError:  # no proxyCertInfo
        return "end entity credential"
    except KeyError:  # no policy language
        return "unidentified proxy"
    else:
        if policy == "1.3.6.1.4.1.3536.1.1.1.9":
            return "RFC 3820 compliant limited proxy"
        if policy == "Inherit all":
            return "RFC 3820 compliant impersonation proxy"
        return "RFC 3820 compliant restricted proxy"


def _get_cert_policy_language(x509):
    for i in range(x509.get_ext_count()):
        ext = x509.get_ext_at(i)
        name = ext.get_name()
        if (
            name == "proxyCertInfo" and
            ext.get_critical()
        ):
            pcidata = dict(
                map(str.strip, line.split(':', 1)) for
                line in ext.get_value().rstrip().split('\n')
            )
            return pcidata["Policy Language"]
    raise ValueError("no policy language found in cert")


def print_cert_info(x509, path=None, verbose=True, stream=sys.stdout):
    """Print info about an X.509 certificate

    Parameters
    ----------
    x509 : `OpenSSL.crypto.X509`
        the certificate to parse

    path : `str`, optional
        the path of the certificate file on disk

    verbose : `bool`, optional
        if `True` (default) print the full text of the certificate

    stream : `file`, optional
        the file object to print to, defaults to `sys.stdout`
    """
    if verbose:
        certstr = crypto.dump_certificate(
            crypto.FILETYPE_PEM,
            x509,
        )
        print(certstr.decode("utf-8"), file=stream, end="")
    pkey = x509.get_pubkey()
    print("subject  : " + _x509_name_str(x509.get_subject()), file=stream)
    print("issuer   : " + _x509_name_str(x509.get_issuer()), file=stream)
    print("type     : " + _cert_type(x509), file=stream)
    print("strength : {0} bits".format(pkey.bits()), file=stream)
    if path:
        print("path     : " + str(path), file=stream)
    remaining = time_left(x509)
    if remaining:
        print(
            "timeleft : " + str(datetime.timedelta(seconds=remaining)),
            file=stream,
        )
    else:
        print("timeleft : 0:00:00 [EXPIRED]", file=stream)


def write_cert(path, pkcs12, use_proxy=False, minhours=168):
    """Write a PKCS12 certificate archive to file in X509 format

    Parameters
    ----------
    path : `str`, `pathlib.Path`
        the desired location of the final X509 file

    pkcs12 : `OpenSSL.crypto.PKCS12`
        a PKCS12 archive

    use_proxy : `bool`, optional
        if `True`, generate an impersonation proxy, otherwise generate
        a standard end entity credential certificate

    minhours : `int`, optional
        the minimum duration of the proxy certificate, only used if
        `proxy=True` is given
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
        shutil.move(tmp.name, str(path))


def generate_proxy(cert, key, minhours=168, limited=False, bits=2048):
    """Generate a proxy certificate based on a certificate

    Based on code from the gridproxy library
    https://github.com/abbot/gridproxy/blob/master/gridproxy/__init__.py
    which is Copyright Lev Shamardin and covered under the GNU GPLv3 license.

    Parameters
    ----------
    cert : `M2Crypto.X509.X509`
        the certificate object

    key : `M2Crypto.RSA.RSA_pub`
        the RSA key object

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
    not_after.set_time(min(not_after_time, cert_not_after_time))
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
