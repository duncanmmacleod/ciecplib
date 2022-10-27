# -*- coding: utf-8 -*-
# Copyright (C) Cardiff University (2019-2022)
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

"""Common testt for ciecplib entry points

Inspired by the test_help module from ligo.skymap.tool.tests,
thanks Leo!
"""

import subprocess

import pytest

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:  # python < 3.8
    importlib_metadata = pytest.importorskip("importlib_metadata")

from ... import (__version__, __name__)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

try:
    ENTRY_POINTS = [
        ep
        for ep in importlib_metadata.distribution(__name__).entry_points
        if ep.group == "console_scripts"
    ]
except importlib_metadata.PackageNotFoundError:
    ENTRY_POINTS = []
PARAMETRIZE_ENTRY_POINTS = pytest.mark.parametrize(
    "ep", [
        pytest.param(ep, id=ep.name)
        for ep in ENTRY_POINTS
    ],
)


def _test_entry_point(ep, args):
    main = ep.load()
    with pytest.raises(SystemExit) as exc:
        main(args)
    if exc.value.code != 0:
        raise subprocess.CalledProcessError(exc.value.code, [ep.name, *args])


@PARAMETRIZE_ENTRY_POINTS
def test_help(ep):
    return _test_entry_point(ep, ['--help'])


@PARAMETRIZE_ENTRY_POINTS
def test_version(capsys, ep):
    _test_entry_point(ep, ['--version'])
    out, err = capsys.readouterr()
    assert out.strip() == __version__
