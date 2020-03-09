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


@pytest.mark.parametrize("side_effect, result", [
    (None, True),
    (CalledProcessError(1, "klist"), False),
])
@mock.patch("subprocess.check_output")
def test_has_credential(mock_output, side_effect, result):
    mock_output.side_effect = side_effect
    assert ciecplib_kerberos.has_credential("klist") is result
