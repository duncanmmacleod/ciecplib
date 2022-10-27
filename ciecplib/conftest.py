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

"""Common fixtures for ciecplib tests
"""

from datetime import (
    datetime,
    timedelta,
)

from cryptography import x509 as crypto_x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.primitives.serialization import Encoding

import pytest


@pytest.fixture(scope="session")  # one per suite is fine
def private_key():
    return generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )


@pytest.fixture(scope="session")
def public_key(private_key):
    return private_key.public_key()


@pytest.fixture
def x509(public_key, private_key):
    name = crypto_x509.Name([
        crypto_x509.NameAttribute(typ, value) for (typ, value) in (
            (crypto_x509.NameOID.COMMON_NAME, "albert einstein"),
            (crypto_x509.NameOID.COUNTRY_NAME, "UK"),
            (crypto_x509.NameOID.STATE_OR_PROVINCE_NAME, "Wales"),
            (crypto_x509.NameOID.LOCALITY_NAME, "Cardiff"),
            (crypto_x509.NameOID.ORGANIZATION_NAME, "Cardiff University"),
            (crypto_x509.NameOID.ORGANIZATIONAL_UNIT_NAME, "Gravity"),
        )
    ])
    now = datetime.utcnow()
    return crypto_x509.CertificateBuilder(
        issuer_name=name,
        subject_name=name,
        public_key=public_key,
        serial_number=1000,
        not_valid_before=now,
        not_valid_after=now + timedelta(seconds=86400),
    ).sign(private_key, hashes.SHA256(), backend=default_backend())


@pytest.fixture
def x509_path(tmp_path, x509):
    path = tmp_path / "tmpx509.pem"
    with path.open("wb") as tmp:
        tmp.write(x509.public_bytes(Encoding.PEM))
    return path
