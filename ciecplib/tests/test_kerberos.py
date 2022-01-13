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

from subprocess import CalledProcessError
from unittest import mock

import pytest

from .. import kerberos as ciecplib_kerberos

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"

KLIST_OUTPUT = b"""
Ticket cache: API:krb5cc
Default principal: test.user@REALM.ORG

Valid starting       Expires              Service principal
01/01/2021 00:00:01  02/01/2021 00:00:01  krbtgt/REALM.ORG@REALM.ORG
""".strip()


@pytest.mark.parametrize("side_effect, result", [
    (None, True),
    (CalledProcessError(1, "klist"), False),
])
@mock.patch("subprocess.check_output")
def test_has_credential(_check_output, side_effect, result):
    _check_output.side_effect = side_effect
    assert ciecplib_kerberos.has_credential("krb5ccname") is result
    _check_output.assert_called_once_with(["klist", "-s", "krb5ccname"])


@mock.patch("subprocess.check_output", return_value=KLIST_OUTPUT)
def test_find_principal(_):
    assert ciecplib_kerberos.find_principal() == "test.user@REALM.ORG"


@mock.patch("subprocess.check_output", return_value=b"")
def test_find_principal_error(_check_output):
    with pytest.raises(RuntimeError) as exc:
        ciecplib_kerberos.find_principal("krb5ccname")
    _check_output.assert_called_once_with(["klist", "krb5ccname"])
    assert str(exc.value) == "failed to parse principal from `klist` output"


def test_realm():
    assert ciecplib_kerberos.realm("marie.curie@EXAMPLE.ORG") == "EXAMPLE.ORG"


def test_realm_error():
    with pytest.raises(ValueError) as exc:
        ciecplib_kerberos.realm("marie.curie")
    assert str(exc.value) == "invalid kerberos principal 'marie.curie'"
