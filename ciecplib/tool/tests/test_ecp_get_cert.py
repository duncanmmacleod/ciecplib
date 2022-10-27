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

"""Tests for :mod:`ciecplib.tool.ecp_get_cert`
"""

from unittest import mock

import pytest

from ... import x509 as ciecplib_x509
from .. import ecp_get_cert


@mock.patch("os.unlink", mock.Mock(side_effect=(None, FileNotFoundError)))
@pytest.mark.parametrize("dummy", (True, False))
def test_destroy(dummy):
    """Check that the --destroy option works whether the file exists or not
    """
    ecp_get_cert.main(["--destroy"])


def test_ecp_get_cert(tmp_path, x509, private_key):
    """Check that a standard workflow correctly writes the key it received.
    """
    x509_path = tmp_path / "x509.pem"
    with mock.patch(
        "ciecplib.tool.ecp_get_cert.get_cert",
        return_value=(x509, private_key),
    ):
        ecp_get_cert.main([
            "--file", str(x509_path),
            "--identity-provider", "test",
        ])
    assert ciecplib_x509.load_cert(x509_path) == x509


@mock.patch("ciecplib.tool.ecp_get_cert.get_cert")
def test_ecp_get_cert_reuse(get_cert, x509_path):
    """Check that the --reuse option works if the key validates.
    """
    # reuse an existing certificate file
    ecp_get_cert.main([
        "--file", str(x509_path),
        "--identity-provider", "test",
        "--reuse",
    ])
    # make sure that it did get reused
    get_cert.assert_not_called()


def test_ecp_get_cert_reuse_fail(x509_path, x509, private_key):
    """Check that the --reuse option works if the key fails to validate.
    """
    bad = x509_path.with_suffix(".bad")
    with mock.patch(
        "ciecplib.tool.ecp_get_cert.get_cert",
        return_value=(x509, private_key),
    ) as mock_get_cert:
        # attempt to reuse an certificate file that doesn't exist
        ecp_get_cert.main([
            "--file", str(bad),
            "--identity-provider", "test",
            "--reuse",
        ])
        # make sure that it did get reused
        mock_get_cert.assert_called_once()
    assert ciecplib_x509.load_cert(bad) == x509
