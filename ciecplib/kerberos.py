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

"""Kerberos utilities for ciecplib
"""

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


def _get_creds(usage="initiate", **kwargs):
    """Return the active GSSAPI credentials, if any.
    """
    try:
        import gssapi
    except ImportError:
        return None
    try:
        return gssapi.Credentials(usage=usage, **kwargs)
    except gssapi.exceptions.GSSError:
        return None


def has_credential(**store_kw):
    """Return `True` if an active Kerberos (GSSAPI) credential is available.

    Parameters
    ----------
    store_kw
        Keyword arguments to pass to the credentials store extension of
        the underlying GSSAPI implementation.
        See https://pythongssapi.github.io/python-gssapi/credstore.html
        for more details.

    Returns
    -------
    True
        If a valid Kerberos credential is found with a lifetime of
        more than 1 second.
    False
        Otherwise.

    Examples
    --------
    >>> has_credential()
    False
    >>> has_credential(
    ...     ccache="mykrb5cc",
    ...     client_keytab="/home/user/.kerberos/me.keytab",
    ... )
    True

    Notes
    -----
    This function will always return `False` if the requests-gssapi
    Kerberos Auth plugin required by requests-ecp is not found.

    See also
    --------
    gssapi.Credentials
        For more details on how credentials are accessed using
        Python-GSSAPI.
    """
    try:
        from requests_ecp.auth import _import_kerberos_auth
    except ImportError:
        # probably requests-ecp < 0.3.0, which always supports kerberos
        pass
    else:
        try:
            _import_kerberos_auth()
        except ImportError:
            # requests-ecp doesn't support Kerberos, so we can't
            return False

    # get credentials and inspect to see if they have a valid liftime
    creds = _get_creds()
    return creds is not None and (creds.lifetime or 0) >= 1


def find_principal():
    """Determine the principal for an active kerberos credential.

    Returns
    -------
    name: `str`
        The `str` representation of the Kerberos principal.

    Raises
    ------
    RuntimeError
        If no credential is found.
    """
    creds = _get_creds()
    if creds is None:
        raise RuntimeError(
            "failed to find active GSSAPI (Kerberos) credential",
        )
    return str(creds.name)


def realm(principal):
    """Return the kerbeos realm name from a principal

    Parameters
    ----------
    principal : `str`
        the kerberos principal to parse

    Returns
    -------
    realm : `str`
        the realm name

    Raises
    ------
    IndexError
        If the input principal cannot be parsed properly
        (normally if it doesn't contain an ``@`` character).

    Examples
    --------
    >>> realm('marie.curie@EXAMPLE.ORG')
    'EXAMPLE.ORG'
    """
    return principal.rsplit("@", 1)[1]
