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

import os
import random
import re
import string
from pathlib import Path
from urllib.parse import urlparse

import requests

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


# -- default paths ------------------------------------------------------------

def _tmpfile(prefix):
    if os.name == "nt":
        tmpdir = r'%SYSTEMROOT%\Temp'
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
_KERBEROS_SUFFIX = " (Kerberos)"
_KERBEROS_REGEX = re.compile(r"{0}\Z".format(re.escape(_KERBEROS_SUFFIX)))


def get_idps(url=DEFAULT_IDPLIST_URL):
    """Download the list of known ECP IdPs from the given URL

    The output is a `dict` where the keys are institution names
    (e.g. ``'Fermi National Accelerator Laboratory'``), and the values
    are the URL of their IdP.

    Some institutions may have two entries if they also support Kerberos.

    Parameters
    ----------
    url : `str`
        the URL of the IDP list file
    """
    idps = dict()
    for line in requests.get(url, stream=True).iter_lines():
        url, inst = line.decode('utf-8').strip().split(' ', 1)
        idps[inst] = url
    return idps


def _match_institution(value, institutions):
    regex = re.compile(r"{0}($| \()".format(value))
    institutions = {_KERBEROS_REGEX.split(name, 1)[0] for name in institutions}
    matches = [inst for inst in institutions if regex.match(inst)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0 and not value.endswith(".*"):
        try:
            return _match_institution("{0}.*".format(value), institutions)
        except ValueError:
            pass
    raise ValueError("failed to identify IdP URLs for {0!r}".format(value))


def get_idp_urls(institution, url=DEFAULT_IDPLIST_URL):
    """Return the regular and Kerberos IdP URLs for a given institution
    """
    idps = get_idps(url=url)
    institution = _match_institution(institution, idps)
    if institution.endswith(_KERBEROS_SUFFIX):
        return None, idps[institution]
    url = idps[institution]
    krbinst = institution + _KERBEROS_SUFFIX
    krburl = idps[krbinst] if krbinst in idps else url
    return url, krburl


def _endpoint_url(url):
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://{0}".format(url)
    if not urlparse(url).path:
        return "{0}/idp/profile/SAML2/SOAP/ECP".format(url)
    return url


def format_endpoint_url(url_or_name, kerberos=False):
    """Format an endpoint reference as a URL

    Parameters
    ----------
    url_or_name: `str`
        the name of an institution, or a URL for the endpoint

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
        if ``url_or_name`` looks like an institution name, but
        cilogon.org doesn't know what the corresponding ECP endpoint URL
        is for that institution.

    Examples
    --------
    >>> format_endpoint_url("LIGO")
    'https://login.ligo.org/idp/profile/SAML2/SOAP/ECP'
    >>> format_endpoint_url("login.myidp.com")
    'https://login.myidp.com/idp/profile/SAML2/SOAP/ECP'
    """
    if url_or_name.count(".") >= 2:  # url
        return _endpoint_url(url_or_name)
    # institution name
    return get_idp_urls(url_or_name)[int(kerberos)]


# -- misc utilities -----------------------------------------------------------

def random_string(length, outof=string.ascii_lowercase+string.digits):
    # http://stackoverflow.com/a/23728630/2213647 says SystemRandom()
    # is most secure
    return ''.join(random.SystemRandom().choice(outof) for _ in range(length))
