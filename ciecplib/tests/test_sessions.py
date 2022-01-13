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

"""Test suite for :mod:`cieclib.sessions`
"""

from unittest import mock

import pytest

from .. import sessions as ciecplib_sessions

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


class TestSession():
    TEST_CLASS = ciecplib_sessions.Session

    @mock.patch("ciecplib.sessions._get_default_idp", lambda: None)
    @mock.patch("ciecplib.sessions.has_krb5_credential", lambda: False)
    def test_init_error(self):
        """Check that the right error is raised when a Session is created
        with no IdP or kerberos credentials
        """
        with pytest.raises(ValueError) as exc:
            self.TEST_CLASS()
        assert str(exc.value).startswith("no Identity Provider")
