# -*- coding: utf-8 -*-
# Copyright (C) Cardiff University (2019-2022)
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
import sys
import tempfile
import time

from cryptography import x509 as crypto_x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"

PROXY_CERT_INFO_EXT_OID = crypto_x509.ObjectIdentifier("1.3.6.1.5.5.7.1.14")

# backport short names for cryptography < 2.5
_NAMEOID_TO_NAME = {
    crypto_x509.NameOID.COMMON_NAME: "CN",
    crypto_x509.NameOID.COUNTRY_NAME: "C",
    crypto_x509.NameOID.DOMAIN_COMPONENT: "DC",
    crypto_x509.NameOID.LOCALITY_NAME: "L",
    crypto_x509.NameOID.ORGANIZATION_NAME: "O",
    crypto_x509.NameOID.ORGANIZATIONAL_UNIT_NAME: "OU",
    crypto_x509.NameOID.STATE_OR_PROVINCE_NAME: "ST",
    crypto_x509.NameOID.STREET_ADDRESS: "STREET",
    crypto_x509.NameOID.USER_ID: "UID",
}


def _parse_unix_time(asn1time):
    """Parse an ASN1 unix time into a python `time` tuple
    """
    return calendar.timegm(asn1time.get_datetime().timetuple())


def load_cert(path):
    """Load an X.509 certificate from file containing PEM-encoded data.

    Parameters
    ----------
    path : `str`, `pathlib.Path`
        the file path from which to read

    Returns
    -------
    cert : `cryptography.x509.Certificate`
        the parsed certificate
    """
    with open(str(path), "rb") as fobj:
        return crypto_x509.load_pem_x509_certificate(
            fobj.read(),
            backend=default_backend(),
        )


def load_pkcs12(raw, password):
    """Load an X.509 certificate and key from a PKCS12 blob.
    """
    try:
        from cryptography.hazmat.primitives.serialization.pkcs12 import (
            load_pkcs12 as _load_pkcs12,
        )
    except ImportError:  # cryptography < 36.0
        from OpenSSL.crypto import load_pkcs12 as _load_pkcs12
        p12 = _load_pkcs12(raw, password)
        return (
            p12.get_certificate().to_cryptography(),
            p12.get_privatekey().to_cryptography_key(),
        )

    p12 = _load_pkcs12(raw, password)
    return (
        p12.cert.certificate,
        p12.key,
    )


def time_left(cert):
    """Returns the number of seconds left on this certificate

    If the certificate has expired, ``0`` is returned.

    Parameters
    ----------
    cert : `cryptography.x509.Certificate`
        The certificate to inspect.
    """
    expiry = cert.not_valid_after.timetuple()
    return max(0, int(calendar.timegm(expiry) - time.time()))


def _x509_name_str(obj):
    """Return the name of the x509 object as a string
    """
    try:
        parts = [x.rfc4514_string() for x in obj.rdns]
    except AttributeError:  # cryptography < 2.5
        parts = [
            f"{_NAMEOID_TO_NAME[attr.oid]}={attr.value}"
            for rdn in obj.rdns
            for attr in rdn
        ]
    return f"/{'/'.join(parts)}"


def check_cert(cert, hours=1, proxy=None, rfc3820=True):
    """Validate an X509 certificate

    Parameters
    ----------
    cert : `cryptography.x509.Certificate`
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
    # parse name entry as common name
    subject = _x509_name_str(x509.subject)
    ntype, name = subject.rsplit("/", 1)[-1].split("=", 1)

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
    except crypto_x509.ExtensionNotFound:
        return "end entity credential"
    except ValueError:  # no policy language
        return "unidentified proxy"
    else:
        if policy == "1.3.6.1.4.1.3536.1.1.1.9":
            return "RFC 3820 compliant limited proxy"
        if policy == "Inherit all":
            return "RFC 3820 compliant impersonation proxy"
        return "RFC 3820 compliant restricted proxy"


def _get_cert_policy_language(x509):
    """Parse the policy language from the proxyCertInfo extension.

    This is a terrible hack because pyca/cryptography doesn't actually support
    the proxyCertInfo extension.
    """
    ext = x509.extensions.get_extension_for_oid(PROXY_CERT_INFO_EXT_OID)
    for line in ext.value.value.split():
        if line.endswith(b"+\x06\x01\x05\x05\x07\x15\x01"):
            return "Inherit all"
        if line.endswith(b"+\x06\x01\x04\x01\x9bP\x01\x01\x01"):
            return "1.3.6.1.4.1.3536.1.1.1.9"
    raise ValueError("no policy language found in cert")


def print_cert_info(
    x509,
    path=None,
    display=None,
    verbose=True,
    stream=sys.stdout,
):
    """Print info about an X.509 certificate

    Parameters
    ----------
    x509 : `cryptography.x509.Certificate`
        the certificate to parse

    path : `str`, optional
        the path of the certificate file on disk

    display : `list`, optional
        list of certificate parameters to display; if given each is displayed
        in order in plaintext

    verbose : `bool`, optional
        if `True` (default) print the full text of the certificate

    stream : `file`, optional
        the file object to print to, defaults to `sys.stdout`
    """
    if display is None:
        display = []
    # parse parameters of certificate
    pkey = x509.public_key()
    remaining = time_left(x509)
    if "timeleft" in display:  # if plaintext, print seconds
        timeleft = str(max(-1, int(remaining)))
    elif remaining:  # otherwise format nicely
        timeleft = str(datetime.timedelta(seconds=remaining))
    else:
        timeleft = "0:00:00 [EXPIRED]"
    params = {
        "subject": _x509_name_str(x509.subject),
        "issuer": _x509_name_str(x509.issuer),
        "type": _cert_type(x509),
        "strength": f"{pkey.key_size} bits",
        "path": path,
        "timeleft": timeleft,
    }
    if verbose or "text" in display:
        params["text"] = "\n" + x509.public_bytes(
            encoding=Encoding.PEM,
        ).decode("utf-8").strip()

    # use chose specific attributes, so just print them in plain text
    if display:
        for attr in display:
            print(params[attr].strip(), file=stream)
    else:
        for attr in params:
            print(f"{attr:9s}: {params[attr]}", file=stream)


def write_cert(path, cert, key, use_proxy=False, minhours=168):
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
    if use_proxy:
        # we will store the original certificate as part of the signing chain
        chain = [cert.public_bytes(encoding=Encoding.PEM)]
        # generate a self-signed proxy
        cert, key = generate_proxy(cert, key, minhours=minhours)
    else:
        chain = []

    # write the cert, key pair, and the signing chain (if any)
    blocks = [
        # the cert
        cert.public_bytes(encoding=Encoding.PEM),
        # the private key associated with the cert's public key
        key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption(),
        ),
    ] + chain

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        # write cert and key to temporary location
        for block in blocks:
            tmp.write(block)
        tmp.close()

        # move tmpfile into place
        shutil.move(tmp.name, str(path))


def generate_proxy(cert, key, minhours=168, limited=False, bits=2048):
    """Generate a proxy certificate based on a certificate.

    Parameters
    ----------
    cert : `cryptography.X509.Certificate`
        The certificate object.

    key : `cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey`
        The RSA key object used to sign the original certificate.

    minhours : `float`
        The minimum lifetime of the proxy certificate. This is bounded by
        the lifetime of the original certificate.

    limited : `bool`
        If `True`, generate a limited proxy.

    bits : `int`
        The number of bits (size) to use for the private key used to sign
        the proxy certificate.

    Returns
    -------
    proxycert : `cryptography.X509.Certificate`
        The proxy certificate.

    proxykey : `cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey`
        The RSA private key used to sign the proxy certificate.
    """
    # generate a new key pair with which to sign the proxy
    proxy_private_key = generate_private_key(
        public_exponent=65537,
        key_size=bits,
        backend=default_backend(),
    )
    proxy_public_key = proxy_private_key.public_key()

    # create a serial number for the proxy
    serial = crypto_x509.random_serial_number()

    # generate a new subject by appending the serial number to
    # the subject of the original certificate
    proxy_subject = crypto_x509.Name(
        list(cert.subject) + [
            crypto_x509.NameAttribute(
                crypto_x509.NameOID.COMMON_NAME,
                str(serial),
            ),
        ]
    )

    # add extensions
    extensions = [crypto_x509.Extension(
        crypto_x509.KeyUsage.oid,
        True,
        crypto_x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=True,
            data_encipherment=True,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        )
    )]
    if limited:
        proxyinfoext = crypto_x509.UnrecognizedExtension(
            PROXY_CERT_INFO_EXT_OID,
            # language:1.3.6.1.4.1.3536.1.1.1.9
            b"0\x0f0\r\x06\x0b+\x06\x01\x04\x01\x9bP\x01\x01\x01\t",
        )
    else:
        proxyinfoext = crypto_x509.UnrecognizedExtension(
            PROXY_CERT_INFO_EXT_OID,
            # language:Inherit all
            b"0\x0c0\n\x06\x08+\x06\x01\x05\x05\x07\x15\x01",
        )

    # build self-signed proxy certificate
    builder = crypto_x509.CertificateBuilder(
        issuer_name=cert.subject,
        subject_name=proxy_subject,
        public_key=proxy_public_key,
        serial_number=serial,
        not_valid_before=cert.not_valid_before,
        not_valid_after=min(
            datetime.datetime.utcnow() + datetime.timedelta(hours=minhours),
            cert.not_valid_after,
        ),
        extensions=extensions,
    ).add_extension(proxyinfoext, critical=True)
    proxy = builder.sign(
        private_key=key,
        algorithm=hashes.SHA256(),
        backend=default_backend(),
    )

    return proxy, proxy_private_key
