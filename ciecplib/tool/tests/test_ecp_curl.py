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

"""Tests for :mod:`ciecplib.tool.ecp_get_curl`.
"""

import pytest

from requests import RequestException

from .. import ecp_curl
from ...cookies import load_cookiejar


def test_main_stdout(capsys, requests_mock):
    """Test ``ecp-curl`` with default options (writes to stdout).
    """
    requests_mock.get(
        "https://test.example.com",
        content=b"hello world",
    )
    # curl the github API top-level URL
    ecp_curl.main([
        "https://test.example.com",
        "--identity-provider", "https://test.example.com/SOAP/ECP",
    ])
    out, err = capsys.readouterr()
    # check that we got valid JSON back
    assert out == "hello world"


def test_main_file(requests_mock, tmp_path):
    """Test ``ecp-curl`` writing to file.
    """
    outfile = tmp_path / "api.github.com.json"
    requests_mock.get(
        "https://test.example.com",
        content=b"hello world",
    )
    # curl the github API top-level URL
    ecp_curl.main([
        "https://test.example.com",
        "--output", str(outfile),
        "--identity-provider", "https://test.example.com/SOAP/ECP",
    ])
    # check that we got valid JSON back
    assert outfile.read_text() == "hello world"


def test_main_error(requests_mock, tmp_path):
    """Test that ``ecp-curl`` propagates RequestExceptions.
    """
    requests_mock.get(
        "https://test.example.com",
        status_code=404,
    )
    with pytest.raises(RequestException):
        ecp_curl.main([
            "https://test.example.com",
            "--identity-provider", "https://test.example.com/SOAP/ECP",
        ])


def test_main_store_cookie_file(capsys, requests_mock, tmp_path):
    """Test that ``ecp-curl`` can store session cookies (sort of).
    """
    jar = tmp_path / "cookies"
    requests_mock.get(
        "https://test.example.com",
        content=b"hello world",
        cookies={"foo": "bar"},
    )

    # curl the github API top-level URL
    ecp_curl.main([
        "https://test.example.com",
        "--store-session-cookies",
        "--cookiefile", str(jar),
        "--identity-provider", "https://test.example.com/SOAP/ECP",
    ])
    out, err = capsys.readouterr()

    # check that we got valid JSON back
    assert out == "hello world"

    # check that we can read the cookie jar
    # (which probably doesn't have any cookies in it)
    load_cookiejar(jar)
