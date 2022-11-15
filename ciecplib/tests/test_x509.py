# -*- coding: utf-8 -*-
# Copyright (C) Cardiff University (2020-2022)
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

"""Test suite for :mod:`cieclib.x509`
"""

import sys
from io import StringIO
from unittest import mock

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

import pytest

from .. import x509 as ciecplib_x509

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"

X509_SUBJECT = (
    "/CN=albert einstein/C=UK/ST=Wales/L=Cardiff/"
    "O=Cardiff University/OU=Gravity"
)


def test_load_cert(x509, x509_path):
    cert = ciecplib_x509.load_cert(x509_path)
    assert cert == x509


def test_load_pkcs12(x509, private_key):
    """Test that `ciecplib.x509.load_pkcs12` returns equivalent certs and keys.
    """
    from cryptography.hazmat.primitives.serialization import (
        BestAvailableEncryption,
    )
    try:
        from cryptography.hazmat.primitives.serialization.pkcs12 import (
            serialize_key_and_certificates,
        )
    except ImportError:  # cryptography < 3.0
        from OpenSSL import crypto
        p12obj = crypto.PKCS12()
        p12obj.set_certificate(crypto.X509.from_cryptography(x509))
        p12obj.set_privatekey(crypto.PKey.from_cryptography_key(private_key))
        p12 = p12obj.export(b"password")
    else:
        p12 = serialize_key_and_certificates(
            b"test",
            private_key,
            x509,
            None,
            BestAvailableEncryption(b"password"),
        )
    cert, key = ciecplib_x509.load_pkcs12(p12, b"password")
    assert cert == x509
    assert key.private_numbers() == private_key.private_numbers()


def test_time_left(x509):
    assert ciecplib_x509.time_left(x509) <= 86400


@mock.patch("ciecplib.x509.time_left", mock.MagicMock(return_value=4000))
def test_check_cert(x509):
    ciecplib_x509.check_cert(x509, hours=1, proxy=False, rfc3820=False)


@mock.patch("ciecplib.x509.time_left", mock.MagicMock(return_value=4000))
def test_check_cert_time(x509):
    with pytest.raises(RuntimeError):
        ciecplib_x509.check_cert(x509, hours=2)


@pytest.mark.parametrize("proxy, certtype", [
    (True, "end entity credential"),
    (False, "some sort of proxy"),
])
@mock.patch("ciecplib.x509._cert_type")
@mock.patch("ciecplib.x509.time_left", mock.MagicMock(return_value=4000))
def test_check_cert_proxy_errors(mock_cert_type, x509, proxy, certtype):
    mock_cert_type.return_value = certtype
    with pytest.raises(RuntimeError):
        ciecplib_x509.check_cert(x509, hours=1, proxy=proxy)


@mock.patch(
    "ciecplib.x509._cert_type",
    mock.MagicMock(return_value="legacy globus proxy"),
)
@mock.patch("ciecplib.x509.time_left", mock.MagicMock(return_value=4000))
def test_check_cert_rfc3820_error(x509):
    with pytest.raises(RuntimeError):
        ciecplib_x509.check_cert(x509, hours=1, rfc3820=True)


@pytest.mark.parametrize("timeleft", (
    pytest.param(0, id="expired"),
    pytest.param(10, id="active"),
))
@mock.patch("ciecplib.x509.time_left")
def test_print_cert_info(mock_time_left, timeleft, x509, capsys):
    mock_time_left.return_value = timeleft
    ciecplib_x509.print_cert_info(
        x509,
        path="test",
        verbose=True,
        stream=sys.stdout,
    )
    out = capsys.readouterr().out.strip()
    assert out.startswith(f"subject  : {X509_SUBJECT}")
    assert "path     : test" in out
    assert ("[EXPIRED]" in out) is (timeleft == 0)
    assert out.endswith("-----END CERTIFICATE-----")


@pytest.mark.parametrize(("display", "result"), [
    (("subject",), X509_SUBJECT),
    (("path", "issuer"), f"test\n{X509_SUBJECT}"),
    (("issuer", "path"), f"{X509_SUBJECT}\ntest"),
])
def test_print_cert_info_display(x509, display, result):
    stream = StringIO()
    ciecplib_x509.print_cert_info(
        x509,
        path="test",
        display=display,
        stream=stream,
    )
    stream.seek(0)
    out = stream.read()
    assert out.strip() == result.strip()


@pytest.mark.parametrize('proxy', (False, True))
def test_write_cert(tmp_path, private_key, x509, proxy):
    path = tmp_path / "509.pem"
    # write the p12 cert to a file
    ciecplib_x509.write_cert(path, x509, private_key, use_proxy=proxy)
    # check that we can read it
    new = ciecplib_x509.load_cert(path)
    # check that we get the same cert back
    if proxy:
        assert new.issuer == x509.subject
        assert ciecplib_x509._x509_name_str(new.subject).startswith(
            ciecplib_x509._x509_name_str(x509.subject),
        )
        assert new.not_valid_after <= x509.not_valid_after
        assert new.not_valid_before >= x509.not_valid_before
        assert new.extensions
    else:
        assert new == x509


@pytest.mark.parametrize("limited, ctype", [
    (False, "RFC 3820 compliant impersonation proxy"),
    (True, "RFC 3820 compliant limited proxy"),
])
def test_generate_proxy(x509, private_key, limited, ctype):
    """Test that :func:`ciecplib.x509.generate_proxy` generates a good proxy.
    """
    # generate a proxy certificate
    proxy, pkey = ciecplib_x509.generate_proxy(
        x509,
        private_key,
        limited=limited,
    )

    # check that the (correct) private_key was used to sign the proxy
    private_key.public_key().verify(
        proxy.signature,
        proxy.tbs_certificate_bytes,
        padding.PKCS1v15(),
        algorithm=hashes.SHA256(),
    )

    # check that the cerificate type matches
    assert ciecplib_x509._cert_type(proxy) == ctype
