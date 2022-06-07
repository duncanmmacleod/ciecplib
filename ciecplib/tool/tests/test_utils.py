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

"""Tests for :mod:`ciecplib.tool.utils`
"""

import argparse
from unittest import mock

import pytest

from ... import __version__ as ciecplib_version
from ...utils import EcpIdentityProvider
from .. import utils as tools_utils

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def test_help_formatter():
    parser = argparse.ArgumentParser(
        formatter_class=tools_utils.HelpFormatter,
    )
    parser.add_argument("test")
    help_ = parser.format_help()
    assert "Usage: " in help_


def test_argument_parser(capsys):
    parser = tools_utils.ArgumentParser()

    # check that HelpFormatter is in place
    assert parser.formatter_class is tools_utils.HelpFormatter

    # check that the version gets parsed
    with pytest.raises(SystemExit):
        parser.parse_args(["--version"])
    assert capsys.readouterr()[0].strip() == ciecplib_version


@mock.patch("ciecplib.tool.utils.find_principal", side_effect=RuntimeError)
@mock.patch.dict("os.environ", clear=True)
def test_argument_parser_kerberos_error(capsys):
    parser = tools_utils.ArgumentParser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--kerberos"])


@mock.patch("ciecplib.tool.utils.find_principal", return_value="user@REALM")
@mock.patch.dict("os.environ", clear=True)
def test_argument_parser_kerberos_defaults(capsys):
    parser = tools_utils.ArgumentParser()
    args = parser.parse_args(["--kerberos"])
    assert args.username == "user"
    assert args.identity_provider == "REALM"


@mock.patch(
    "ciecplib.tool.utils.get_idps",
    return_value=[
        EcpIdentityProvider("Inst 1", "https://url1", False),
        EcpIdentityProvider("Cardiff University", "https://cardiff", True),
    ],
)
def test_list_idps_action(_, capsys):
    parser = tools_utils.ArgumentParser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--list-idps"])
    stdout = capsys.readouterr()[0]
    assert "'Cardiff University'" in stdout
