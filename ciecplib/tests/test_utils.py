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
INSTITUTIONS = {
    "Institution 1": "https://inst1.test",
    "Institution 1 (Kerberos)": "https://inst1.test.krb",
    "Institution 2": "https://inst2.test",
}
RAW_IDP_LIST = "\n".join(
    (" ".join((y, x)) for (x, y) in INSTITUTIONS.items()),
).encode()


@mock.patch(
    "os.getlogin" if os.name == "nt" else "os.getuid",
    mock.MagicMock(return_value=123),
)
def test_get_ecpcookie_path():
    if os.name == "nt":
        path = r"%SYSTEMROOT%\Temp\ecpcookie.123"
    else:
        path = "/tmp/ecpcookie.u123"
    assert ciecplib_utils.get_ecpcookie_path() == Path(path)


@mock.patch(
    "os.getlogin" if os.name == "nt" else "os.getuid",
    mock.MagicMock(return_value=123),
)
def test_get_x509_proxy_path():
    if os.name == "nt":
        path = r"%SYSTEMROOT%\Temp\x509up_123"
    else:
        path = "/tmp/x509up_u123"
    assert ciecplib_utils.get_x509_proxy_path() == Path(path)


def test_get_idps(requests_mock):
    requests_mock.get("https://idp-list-url", content=RAW_IDP_LIST)
    assert ciecplib_utils.get_idps("https://idp-list-url") == INSTITUTIONS


@pytest.mark.parametrize("inst, result", [
    ("Institution 1", (
        INSTITUTIONS["Institution 1"],
        INSTITUTIONS["Institution 1 (Kerberos)"],
    )),
    ("Institution 2", (INSTITUTIONS["Institution 2"],) * 2),
])
def test_get_idp_urls(requests_mock, inst, result):
    requests_mock.get("https://idp-list-url", content=RAW_IDP_LIST)
    assert ciecplib_utils.get_idp_urls(
        inst,
        url="https://idp-list-url",
    ) == result


@pytest.mark.parametrize("inst", ["Institution*", "something else"])
def test_get_idp_urls_error(requests_mock, inst):
    requests_mock.get("https://idp-list-url", content=RAW_IDP_LIST)
    with pytest.raises(ValueError):
        ciecplib_utils.get_idp_urls(inst, url="https://idp-list-url")


@pytest.mark.parametrize("url, result", [
    ("login.ligo.org",
     "https://login.ligo.org/idp/profile/SAML2/SOAP/ECP"),
    ("https://login.ligo.org",
     "https://login.ligo.org/idp/profile/SAML2/SOAP/ECP"),
    ("login.ligo.org/test",
     "https://login.ligo.org/test"),
    ("https://login.ligo.org/idp/profile/SAML2/SOAP/ECP",
     "https://login.ligo.org/idp/profile/SAML2/SOAP/ECP"),
])
def test_format_endpoint_url(url, result):
    assert ciecplib_utils.format_endpoint_url(url) == result
