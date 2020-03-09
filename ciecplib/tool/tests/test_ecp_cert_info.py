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

"""Tests for :mod:`ciecplib.tool.ecp_cert_info`
"""

from unittest import mock

import pytest

from .. import ecp_cert_info


@mock.patch("ciecplib.tool.ecp_cert_info.load_cert", mock.Mock())
@mock.patch("ciecplib.tool.ecp_cert_info.print_cert_info", mock.Mock())
@mock.patch(
    "ciecplib.tool.ecp_cert_info.time_left",
    mock.Mock(side_effect=(3700., 3500.)),
)
def test_valid():
    """Check that the --valid option for ecp-cert-info works
    """
    ecp_cert_info.main(["--valid", "1:0"])
    with pytest.raises(AssertionError):
        ecp_cert_info.main(["--valid", "1:0"])
