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

"""Test suite for :mod:`ciecplib.cookies`
"""

from http.cookiejar import Cookie
try:
    from http.cookiejar import NETSCAPE_HEADER_TEXT
except ImportError:  # python < 3.10
    from http.cookiejar import MozillaCookieJar
    NETSCAPE_HEADER_TEXT = MozillaCookieJar.header

import pytest

from ciecplib import cookies as ciecplib_cookies


@pytest.fixture
def sessioncookie():
    return Cookie(
        version=0,
        name="_shibsession_1234567890",
        value="_1234567890",
        port=None,
        port_specified=False,
        domain="somewhere.test.com",
        domain_specified=False,
        domain_initial_dot=False,
        path="/",
        path_specified=True,
        secure=True,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={"HttpOnly": None},
        rfc2109=False,
    )


@pytest.fixture
def ecpcookiejar(sessioncookie):
    jar = ciecplib_cookies.ECPCookieJar()
    jar.set_cookie(sessioncookie)
    return jar


class TestECPCookieJar(object):
    TEST_CLASS = ciecplib_cookies.ECPCookieJar

    def test_save_discard(self, ecpcookiejar, tmp_path):
        path = tmp_path / "cookies"
        ecpcookiejar.save(path)
        # check that the header got written
        assert path.read_text().startswith(NETSCAPE_HEADER_TEXT)
        # check that there aren't actually any cookies
        # (since the cookie is a session cookie [`discard=True`])
        jar = self.TEST_CLASS()
        jar.load(str(path))
        assert len(jar) == 0

    def test_save_ignore_discard(self, ecpcookiejar, tmp_path):
        path = tmp_path / "cookies"
        ecpcookiejar.save(path, ignore_discard=True, ignore_expires=True)
        jar = self.TEST_CLASS()
        jar.load(str(path), ignore_discard=True, ignore_expires=True)
        assert jar["_shibsession_1234567890"] == "_1234567890"


def test_extract_session_cookie(ecpcookiejar, sessioncookie):
    assert ciecplib_cookies.extract_session_cookie(
        ecpcookiejar,
        "https://somewhere.test.com/blah/blah",
    ) is sessioncookie


def test_extract_session_cookie_error(ecpcookiejar):
    with pytest.raises(ValueError):
        ciecplib_cookies.extract_session_cookie(
            ecpcookiejar,
            "https://somethingelse.test.com",
        )


@pytest.mark.parametrize("url, result", [
    ("https://somewhere.test.com", True),
    ("https://somewhereelse.test.com", False),
])
def test_has_session_cookies(ecpcookiejar, url, result):
    assert ciecplib_cookies.has_session_cookies(ecpcookiejar, url) is result


def test_load_cookiejar(ecpcookiejar, tmp_path):
    path = tmp_path / "cookies"
    ecpcookiejar.save(path, ignore_discard=True, ignore_expires=True)
    jar = ciecplib_cookies.load_cookiejar(path)
    assert jar == ecpcookiejar


def test_load_cookiejar_error(tmp_path):
    with pytest.raises(OSError):
        ciecplib_cookies.load_cookiejar(tmp_path / "blah")
    assert isinstance(
        ciecplib_cookies.load_cookiejar(tmp_path / "blah", strict=False),
        ciecplib_cookies.ECPCookieJar,
    )
