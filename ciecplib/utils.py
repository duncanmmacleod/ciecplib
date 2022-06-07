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

import os
import random
import re
import string
from collections import namedtuple
from pathlib import Path

import requests

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


# -- default paths ------------------------------------------------------------

def _tmpfile(prefix):
    if os.name == "nt":
        tmpdir = Path(os.environ["SYSTEMROOT"]) / "Temp"
        user = os.getlogin()
    else:
        tmpdir = "/tmp"
        user = "u{}".format(os.getuid())
    return Path(tmpdir) / "{}{}".format(prefix, user)


def get_ecpcookie_path():
    """Returns the default path for the ECP cookie file

    Returns
    -------
    path : `pathlib.Path`
    """
    return _tmpfile("ecpcookie.")


def get_x509_proxy_path():
    """Returns the default path for the X.509 certificate file

    Returns
    -------
    path : `pathlib.Path`
    """
    if os.getenv("X509_USER_PROXY"):
        return Path(os.environ["X509_USER_PROXY"])
    return _tmpfile("x509up_")


DEFAULT_COOKIE_FILE = str(get_ecpcookie_path())
DEFAULT_X509_USER_FILE = str(get_x509_proxy_path())

# -- institution URLs ----------------------------------------------------

DEFAULT_IDPLIST_URL = "https://cilogon.org/include/ecpidps.txt"
DEFAULT_SP_URL = "https://ecp.cilogon.org/secure/getcert"
_ECP_ENDPOINT_REGEX = re.compile(r"\Ahttps://.*/SOAP/ECP\Z")
_KERBEROS_SUFFIX = " (Kerberos)"
_PRIMARY_SUFFIX_REGEX = re.compile(r" (\()?({})(\))?\Z".format("|".join((
    "1",
    "main",
    "primary",
    "principal",
))))
_SECONDARY_SUFFIX_REGEX = re.compile(r" (\()?({})(\))?\Z".format("|".join((
    "[2-9]",
    "[0-9][0-9]+",
    "backup",
    "secondary",
    "test",
))))
_URL_REGEX = re.compile(r"[^ \t\n\r\f\vA-Z]+")


EcpIdentityProvider = namedtuple(
    "IdP",
    (
        'name',
        'url',
        'iskerberos',
    ),
)


def get_idps(url=DEFAULT_IDPLIST_URL):
    """Download the list of known ECP IdPs from the given URL

    The output is a `list` of `EcpIdentityProvider` objects.

    Some institutions may have two entries if they also support Kerberos.

    Parameters
    ----------
    url : `str`
        the URL of the IDP list file
    """
    idps = list()
    for line in requests.get(url, stream=True).iter_lines():
        url, inst = line.decode('utf-8').strip().split(' ', 1)
        idps.append(EcpIdentityProvider(
            inst,
            url,
            inst.endswith(_KERBEROS_SUFFIX),
        ))
    return idps


def _match(value, idplist, attr, kerberos=None):
    return [
        inst for inst in idplist
        if value in getattr(inst, attr).lower()
        and kerberos in (None, inst.iskerberos)
    ]


def _preferred_match(matches):
    """Attempt to select a preferred match from a list of many

    This only prefers institutions names that don't end with a
    numeric suffix (or end with ' 1'), mainly to distinguish
    between multiple entries like ``'Cardiff University 1'`` and
    ``'Cardiff University 2'``
    """
    if not len(matches) > 1:
        return matches
    # find all names marked as 'primary' or similar
    primaries = [x for x in matches if _PRIMARY_SUFFIX_REGEX.search(x.name)]
    # find all names marked as 'backup' or similar
    secondaries = [x for x in matches if
                   _SECONDARY_SUFFIX_REGEX.search(x.name)]
    # if only one primary, return that
    if len(primaries) == 1:
        return primaries[:1]
    # if all secondary, bar one, return that
    if len(secondaries) == len(matches) - 1:
        return [(set(matches) - set(secondaries)).pop()]
    # otherwise no preference, return everything
    return matches


def _match_institution(value, institutions, kerberos=None):
    value = str(value).lower()

    # try and match the institution name
    matches = _preferred_match(
        _match(value, institutions, "name", kerberos=kerberos),
    )
    if len(matches) == 1:
        return matches.pop()

    # otherwise match the IdP URL
    if _URL_REGEX.match(value):
        umatches = _preferred_match(
            _match(value, institutions, "url", kerberos=kerberos),
        )
        if len(umatches) == 1:
            return umatches.pop()
        matches = matches or umatches or []

    # if we found multiple matches, print them to help the user
    if len(matches):
        raise ValueError(
            "failed to identify unique IdP URL for {0!r}, possible matches "
            "include:\n"
            "{1}".format(
                value,
                "\n".join(map("{0.name!r}: {0.url}".format, matches)),
            ),
        )

    # otherwise just fail
    raise ValueError("failed to identify IdP URLs for {0!r}".format(value))


def get_idp_url(url_or_name, idplist_url=DEFAULT_IDPLIST_URL, kerberos=False):
    """Return the unique IdP URL for a given institution or URL stub

    Parameters
    ----------
    url_or_name: `str`
        the name of an institution, or a URL for the endpoint, or part thereof

    idplist_url : `str`, optional
        the URL to query for the list of enabled ECP IdPs

    kerberos : `bool`, optional
        if ``True`` return a Kerberos URL, if available, otherwise return
        a standard SAML/ECP endpoint URL

    Returns
    -------
    url : `str`
        the formatted URL of the IdP ECP endpoint

    Raises
    ------
    ValueError
        if there isn't a unique match for either the institution name, or the
        IdP URL

    Examples
    --------
    >>> get_idp_url("LIGO")
    'https://login.ligo.org/idp/profile/SAML2/SOAP/ECP'
    >>> get_idp_url("ligo.org")
    'https://login.ligo.org/idp/profile/SAML2/SOAP/ECP'
    """
    # short circuit full URLs
    if _ECP_ENDPOINT_REGEX.match(url_or_name):
        return url_or_name
    # otherwise match against CILogon's registered list
    idps = get_idps(url=idplist_url)
    institution = _match_institution(url_or_name, idps, kerberos=kerberos)
    return institution.url


# -- misc utilities -----------------------------------------------------------

def random_string(length, outof=string.ascii_lowercase + string.digits):
    # http://stackoverflow.com/a/23728630/2213647 says SystemRandom()
    # is most secure
    return ''.join(random.SystemRandom().choice(outof) for _ in range(length))
