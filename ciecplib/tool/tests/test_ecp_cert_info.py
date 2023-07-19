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

"""Tests for :mod:`ciecplib.tool.ecp_cert_info`
"""

from unittest import mock

import pytest

from .. import ecp_cert_info
from ...x509 import _x509_name_str as x509_name_str

MOD_PATH = ecp_cert_info.__name__


@mock.patch(f"{ecp_cert_info.__name__}.load_cert", mock.Mock())
@mock.patch(f"{ecp_cert_info.__name__}.print_cert_info", mock.Mock())
@mock.patch(
    f"{ecp_cert_info.__name__}.time_left",
    mock.Mock(side_effect=(3700., 3500.)),
)
def test_valid():
    """Check that the --valid option for ecp-cert-info works
    """
    ecp_cert_info.main(["--valid", "1:0"])
    with pytest.raises(ValueError):
        ecp_cert_info.main(["--valid", "1:0"])


@mock.patch(f"{ecp_cert_info.__name__}.load_cert")
def test_main(load_cert, capsys, x509):
    load_cert.return_value = x509
    ecp_cert_info.main([])
    out = capsys.readouterr().out
    assert out.startswith("subject  : /CN=albert einstein/C=UK")


@mock.patch(f"{ecp_cert_info.__name__}.load_cert", mock.Mock())
@mock.patch(f"{ecp_cert_info.__name__}.time_left")
@pytest.mark.parametrize(("remaining", "code"), [
    (3700, 0),
    (3500, 1),
])
def test_exists(time_left, remaining, code):
    time_left.return_value = remaining
    assert ecp_cert_info.main(["--exists", "--valid", "1:0"]) == code


@mock.patch(f"{ecp_cert_info.__name__}.load_cert")
def test_display(load_cert, x509, capsys):
    """Check that the display option works
    """
    load_cert.return_value = x509
    ecp_cert_info.main(["-subject"])
    out = capsys.readouterr().out
    assert out.strip() == x509_name_str(x509.subject)
