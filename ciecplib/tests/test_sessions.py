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

import logging

import pytest

from .. import sessions as ciecplib_sessions

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


class TestSession():
    TEST_CLASS = ciecplib_sessions.Session

    def test_init_error(self):
        """Check that the right error is raised when a Session is created
        with no IdP or kerberos credentials
        """
        with pytest.raises(ValueError) as exc:
            self.TEST_CLASS(idp=None, kerberos=False)
        assert str(exc.value).startswith("no Identity Provider")

    @pytest.mark.parametrize("debug", (False, True))
    def test_debug(self, debug):
        """Check that the ``debug`` keyword argument is handled properly
        """
        sess = self.TEST_CLASS(
            idp="https://example.com/idp/profile/SAML2/SOAP/ECP",
            kerberos=False,
            debug=debug,
        )
        # check that the parameter was recorded properly
        assert sess.debug is debug
        # check that the level was propagated up to the root logger properly
        assert logging.getLogger().isEnabledFor(logging.DEBUG) is debug
        # check that closing does the right thing
        sess.close()
        assert (
            # either debug is disabled
            logging.getLogger().isEnabledFor(logging.DEBUG) is False
            # or the logger was set back to NOTSET
            or logging.getLogger().getEffectiveLevel() == logging.NOTSET
        )
