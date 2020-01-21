# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2019)
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

"""Tests for :mod:`ciecplib.utils`
"""

import argparse
try:
    from urllib.error import URLError
except ImportError:  # python < 3
    from urllib2 import URLError

import pytest

from ... import __version__ as ciecplib_version
from .. import utils as tools_utils

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def test_help_formatter():
    parser = argparse.ArgumentParser(
        formatter_class=tools_utils.HelpFormatter,
    )
    parser.add_argument("test")
    help = parser.format_help()
    assert "Usage: " in help


def test_argument_parser(capsys):
    parser = tools_utils.ArgumentParser()

    # check that HelpFormatter is in place
    assert parser.formatter_class is tools_utils.HelpFormatter

    # check that the version gets parsed
    with pytest.raises(SystemExit):
        parser.parse_args(["--version"])
    assert capsys.readouterr().out.strip() == ciecplib_version


def test_list_idps_action(capsys):
    parser = tools_utils.ArgumentParser()
    with pytest.raises(SystemExit):
        try:
            parser.parse_args(["--list-idps"])
        except URLError as exc:
            pytest.skip(str(exc))
    stdout = capsys.readouterr().out
    assert "'Cardiff University'" in stdout
