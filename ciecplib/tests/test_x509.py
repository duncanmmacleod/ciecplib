# -*- coding: utf-8 -*-
# Copyright (C) Cardiff University (2020)
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
from unittest import mock

import pytest

from .. import x509 as ciecplib_x509

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"

X509_HASH = 967391982


def test_load_cert(x509_path):
    x509 = ciecplib_x509.load_cert(x509_path)
    assert x509.get_subject().hash() == X509_HASH


@pytest.mark.parametrize("lib", ("openssl", "m2crypto"))
def test_time_left(x509, x509_m2, lib):
    cert = {
        "openssl": x509,
        "m2crypto": x509_m2,
    }[lib]
    assert ciecplib_x509.time_left(cert) <= 86400


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
    out = capsys.readouterr().out
    assert out.startswith("-----BEGIN CERTIFICATE-----")
    assert (
        "subject  : /CN=albert einstein/C=UK/ST=Wales/L=Cardiff"
        "/O=Cardiff University/OU=Gravity"
    ) in out
    assert "path     : test" in out
    assert ("[EXPIRED]" in out) is (timeleft == 0)


@pytest.mark.parametrize('proxy', (False, True))
def test_write_cert(tmp_path, pkcs12, proxy):
    path = tmp_path / "509.pem"
    # write the p12 cert to a file
    ciecplib_x509.write_cert(path, pkcs12, use_proxy=proxy)
    # check that we can read it
    assert (
        ciecplib_x509.load_cert(path).get_issuer().hash()
    ) == X509_HASH


@pytest.mark.parametrize("limited, ctype", [
    (False, "RFC 3820 compliant impersonation proxy"),
    (True, "RFC 3820 compliant limited proxy"),
])
def test_generate_proxy(pkey_m2, x509_m2, limited, ctype):
    proxy, pkey = ciecplib_x509.generate_proxy(
        x509_m2,
        pkey_m2.get_rsa(),
        limited=limited,
    )
    assert ciecplib_x509._cert_type(proxy) == ctype
