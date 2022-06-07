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

"""Tests for :mod:`ciecplib.utils`
"""

import os
from pathlib import Path
from unittest import mock

import pytest

from .. import utils as ciecplib_utils

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

EcpIdP = ciecplib_utils.EcpIdentityProvider

# mock response from ECP IdP list
INST_DICT = {
    "Institution A": "https://login.insta.org/idp/profile/SAML2/SOAP/ECP",
    "Institution A (Kerberos)":
        "https://login.insta.krb/idp-krb/profile/SAML2/SOAP/ECP",
    "Institution B": "https://login.instb.org/idp/profile/SAML2/SOAP/ECP",
    "Institution C": "https://login.instc.org/idp/profile/SAML2/SOAP/ECP",
    "Institution C (backup)":
        "https://login2.instc.org/idp/profile/SAML2/SOAP/ECP",
}
INSTITUTIONS = [
    EcpIdP(
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
    # direct match for institution
    ("Institution A", False, INST_DICT["Institution A"]),
    ("Institution A (Kerberos)", None, INST_DICT["Institution A (Kerberos)"]),
    # kerberos selection
    ("Institution A", True, INST_DICT["Institution A (Kerberos)"]),
    # partial match for URL
    ("insta", False, INST_DICT["Institution A"]),
    ("login.insta.krb", None, INST_DICT["Institution A (Kerberos)"]),
    ("instb", None, INST_DICT["Institution B"]),
    # valid ECP URL, just return it
    ("https://myidp.org/idp/profile/SAML2/SOAP/ECP", None,
     "https://myidp.org/idp/profile/SAML2/SOAP/ECP"),
    # preferred match based on institution name
    ("Institution C", None, INST_DICT["Institution C"]),
    # preferred match based on URL
    ("instc", None, INST_DICT["Institution C"]),
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
    # name too vague, multiple matches
    "Institution",
    # URL too vague, multiple matches
    "login",
    # no matches
    "something else",
])
def test_get_idp_url_error(requests_mock, inst):
    requests_mock.get("https://idp-list-url", content=RAW_IDP_LIST)
    with pytest.raises(ValueError):
        ciecplib_utils.get_idp_url(inst, idplist_url="https://idp-list-url")


@pytest.mark.parametrize("matches, out", (
    # match one primary
    ([EcpIdP("Inst (main)", "", False), EcpIdP("Inst (backup)", "", False)],
     [EcpIdP("Inst (main)", "", False)]),
    ([EcpIdP("Inst (primary)", "", False), EcpIdP("Inst (backup)", "", False)],
     [EcpIdP("Inst (primary)", "", False)]),
    ([EcpIdP("Inst 1", "", False), EcpIdP("Inst 2", "", False)],
     [EcpIdP("Inst 1", "", False)]),
    # match all-bar-one secondaries
    ([EcpIdP("Inst", "", False), EcpIdP("Inst 2", "", False)],
     [EcpIdP("Inst", "", False)]),
    # no match, return both
    ([EcpIdP("Inst A", "", False), EcpIdP("Inst B", "", False)],
     [EcpIdP("Inst A", "", False), EcpIdP("Inst B", "", False)]),
))
def test_preferred_match(matches, out):
    assert ciecplib_utils._preferred_match(matches) == out
