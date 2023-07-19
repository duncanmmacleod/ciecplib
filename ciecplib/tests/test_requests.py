# -*- coding: utf-8 -*-
# Copyright (C) Cardiff University (2022)
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

"""Tests for :mod:`ciecplib.requests`
"""

from .. import requests as ciecplib_requests

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def test_get(requests_mock):
    requests_mock.get("https://test.example.com", content=b"HELLO")
    assert ciecplib_requests.get(
        "https://test.example.com",
        endpoint="https://test.example.com/SOAP/ECP",
        kerberos=False,
    ).text == "HELLO"
