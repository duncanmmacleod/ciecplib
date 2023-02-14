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

from unittest import mock

import pytest

from .. import kerberos as ciecplib_kerberos

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


@pytest.mark.parametrize(("lifetime", "result"), [
    (None, False),
    (0, False),
    (1, True),
])
@mock.patch("gssapi.Credentials")
def test_has_credential(creds, lifetime, result):
    # check we can import things
    gssapi = pytest.importorskip("gssapi")
    pytest.importorskip("requests_gssapi")

    # mock the credential
    creds.return_value.name = gssapi.Name(
        "marie.curie@LIGO.ORG",
        name_type=gssapi.NameType.kerberos_principal,
    )
    creds.return_value.lifetime = lifetime

    # assert the result
    assert ciecplib_kerberos.has_credential() is result


@mock.patch.dict("sys.modules", {"gssapi": None})
def test_has_credential_no_gssapi():
    assert not ciecplib_kerberos.has_credential()


@mock.patch("requests_ecp.auth._import_kerberos_auth", side_effect=ImportError)
def test_has_credential_no_kerberos_auth(_):
    assert not ciecplib_kerberos.has_credential()


@mock.patch("gssapi.Credentials")
def test_find_principal(creds):
    gssapi = pytest.importorskip("gssapi")
    # mock the credential
    creds.return_value.name = gssapi.Name(
        "marie.curie@LIGO.ORG",
        name_type=gssapi.NameType.kerberos_principal,
    )
    assert ciecplib_kerberos.find_principal() == "marie.curie@LIGO.ORG"


@mock.patch.dict("sys.modules", {"gssapi": None})
def test_find_principal_no_gssapi():
    with pytest.raises(RuntimeError):
        assert ciecplib_kerberos.find_principal()


@mock.patch("gssapi.Credentials")
def test_find_principal_no_creds(creds):
    gssapi = pytest.importorskip("gssapi")
    creds.side_effect = gssapi.exceptions.GSSError(0, 0)
    with pytest.raises(RuntimeError):
        assert ciecplib_kerberos.find_principal()


def test_realm():
    assert ciecplib_kerberos.realm("marie.curie@EXAMPLE.ORG") == "EXAMPLE.ORG"


@pytest.mark.parametrize("principal", [
    "marie.curie",
    "test/robot",
    "",
])
def test_realm_error(principal):
    with pytest.raises(IndexError):
        ciecplib_kerberos.realm(principal)
