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

"""Common fixtures for ciecplib tests
"""

from OpenSSL import crypto
from M2Crypto import (
    X509 as m2X509,
    EVP as m2EVP,
)

import pytest


@pytest.fixture
def pkey():
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 1024)
    return key


@pytest.fixture
def x509(pkey):
    cert = crypto.X509()
    sub = cert.get_subject()
    sub.CN = "albert einstein"
    sub.C = "UK"
    sub.ST = "Wales"
    sub.L = "Cardiff"
    sub.O = "Cardiff University"  # noqa: E741
    sub.OU = "Gravity"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(86400)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(pkey)
    cert.sign(pkey, "sha256")
    return cert


@pytest.fixture
def x509_path(tmp_path, x509):
    path = tmp_path / "tmpx509.pem"
    with path.open("wb") as tmp:
        tmp.write(crypto.dump_certificate(crypto.FILETYPE_PEM, x509))
    return path


@pytest.fixture
def x509_m2(x509):
    return m2X509.load_cert_string(
        crypto.dump_certificate(crypto.FILETYPE_PEM, x509),
    )


@pytest.fixture
def pkey_m2(pkey):
    return m2EVP.load_key_string(
        crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey),
    )


@pytest.fixture
def pkcs12(pkey, x509):
    p12 = crypto.PKCS12()
    p12.set_privatekey(pkey)
    p12.set_certificate(x509)
    return p12
