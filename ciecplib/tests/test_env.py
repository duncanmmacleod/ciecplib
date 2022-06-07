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

import os
from unittest import mock

import pytest

from .. import env as ciecplib_env

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


@pytest.mark.parametrize("env, result", [
    ({}, None),
    ({"ECP_IDP": "TEST"}, "TEST"),
    ({"CIGETCERTOPTS": "-i TEST2"}, "TEST2"),
])
@mock.patch.dict('os.environ', clear=True)
def test_get_default_idp(env, result):
    os.environ.update(env)
    assert ciecplib_env._get_default_idp() == result
