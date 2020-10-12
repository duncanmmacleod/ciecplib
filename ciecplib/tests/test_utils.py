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

"""Tests for :mod:`ciecplib.utils`
"""

import os
from pathlib import Path
from unittest import mock

import pytest

from .. import utils as ciecplib_utils

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

# mock response from ECP IdP list
INST_DICT = {
    "Institution 1": "https://inst1.test/idp/profile/SAML2/SOAP/ECP",
    "Institution 1 (Kerberos)":
        "https://inst1.test.krb/idp-krb/profile/SAML2/SOAP/ECP",
    "Institution 2": "https://inst2.test/idp/profile/SAML2/SOAP/ECP",
}
INSTITUTIONS = [
    ciecplib_utils.EcpIdentityProvider(
        name,
        url,
        name.endswith("(Kerberos)"),
    ) for name, url in INST_DICT.items()
]
RAW_IDP_LIST = "\n".join(map("{0.url} {0.name}".format, INSTITUTIONS)).encode()


@mock.patch(
    "os.getlogin" if os.name == "nt" else "os.getuid",
    mock.MagicMock(return_value=123),
)
@mock.patch.dict("os.environ")
def test_get_ecpcookie_path():
    if os.name == "nt":
        path = r"C:\WINDOWS\Temp\ecpcookie.123"
    else:
        path = "/tmp/ecpcookie.u123"
    assert ciecplib_utils.get_ecpcookie_path() == Path(path)


@mock.patch(
    "os.getlogin" if os.name == "nt" else "os.getuid",
    mock.MagicMock(return_value=123),
)
def test_get_x509_proxy_path():
    os.environ.pop("X509_USER_PROXY", None)
    if os.name == "nt":
        path = r"C:\WINDOWS\Temp\x509up_123"
    else:
        path = "/tmp/x509up_u123"
    assert ciecplib_utils.get_x509_proxy_path() == Path(path)


def test_get_idps(requests_mock):
    requests_mock.get("https://idp-list-url", content=RAW_IDP_LIST)
    assert ciecplib_utils.get_idps("https://idp-list-url") == INSTITUTIONS


@pytest.mark.parametrize("value, krb, result", [
    ("Institution 1", False, INST_DICT["Institution 1"]),
    ("Institution 1 (Kerberos)", None,
     INST_DICT["Institution 1 (Kerberos)"]),
    ("Institution 1", True, INST_DICT["Institution 1 (Kerberos)"]),
    ("inst1", False, INST_DICT["Institution 1"]),
    ("inst1.test.krb", None, INST_DICT["Institution 1 (Kerberos)"]),
    ("inst2", None, INST_DICT["Institution 2"]),
    ("https://inst1.test/idp/profile/SAML2/SOAP/ECP", None,
     INST_DICT["Institution 1"]),
])
def test_get_idp_url(requests_mock, value, krb, result):
    # only proxy idp-list-url if we need to
    if not value.endswith(r"/ECP"):
        requests_mock.get("https://idp-list-url", content=RAW_IDP_LIST)
    assert ciecplib_utils.get_idp_url(
        value,
        idplist_url="https://idp-list-url",
        kerberos=krb,
    ) == result


@pytest.mark.parametrize("inst", [
    "Institution*",
    "test",
    "something else",
])
def test_get_idp_url_error(requests_mock, inst):
    requests_mock.get("https://idp-list-url", content=RAW_IDP_LIST)
    with pytest.raises(ValueError):
        ciecplib_utils.get_idp_url(inst, idplist_url="https://idp-list-url")
