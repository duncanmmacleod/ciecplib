# -*- coding: utf-8 -*-
# Copyright (C) Cardiff University (2019-2020)
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

try:
    from unittest import mock
except ImportError:  # python < 3
    import mock
    urlreqmodname = "urllib2"
else:
    urlreqmodname = "urllib.request"

import pytest

from .. import utils as ciecplib_utils

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

RAW_INSTITUTION_LIST = [
    b"https://inst1.test Institution 1",
    b"https://inst2.test Institution 2",
]


@mock.patch(
    "{0}.urlopen".format(urlreqmodname),
    return_value=RAW_INSTITUTION_LIST,
)
def test_get_idps(urlopen):
    assert ciecplib_utils.get_idps("something") == {
        "Institution 1": "https://inst1.test",
        "Institution 2": "https://inst2.test",
    }
    assert urlopen.called_with("something")


@mock.patch(
    "{0}.urlopen".format(urlreqmodname),
    return_value=RAW_INSTITUTION_LIST,
)
def test_get_idp_urls(_):
    assert ciecplib_utils.get_idp_urls("Institution 1") == (
        "https://inst1.test",
        "https://inst1.test",
    )


@mock.patch(
    "{0}.urlopen".format(urlreqmodname),
    return_value=RAW_INSTITUTION_LIST,
)
@pytest.mark.parametrize("inst", ["Institution*", "something else"])
def test_get_idp_urls_error(_, inst):
    with pytest.raises(ValueError):
        ciecplib_utils.get_idp_urls(inst)


@pytest.mark.parametrize("url, result", [
    ("login.ligo.org",
     "https://login.ligo.org/idp/profile/SAML2/SOAP/ECP"),
    ("https://login.ligo.org",
     "https://login.ligo.org/idp/profile/SAML2/SOAP/ECP"),
    ("login.ligo.org/test",
     "https://login.ligo.org/test"),
    ("https://login.ligo.org/idp/profile/SAML2/SOAP/ECP",
     "https://login.ligo.org/idp/profile/SAML2/SOAP/ECP"),
])
def test_format_endpoint_url(url, result):
    assert ciecplib_utils.format_endpoint_url(url) == result
