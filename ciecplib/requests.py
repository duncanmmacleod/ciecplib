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

"""HTTP request method with end-to-end ECP authentication
"""

from functools import wraps

from .env import DEFAULT_IDP
from .sessions import Session

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


def _ecp_session(func):
    """Decorate a function to open a `requests_ecp.Session`
    """
    @wraps(func)
    def _wrapper(*args, **kwargs):
        if kwargs.get('session') is None:
            kwargs['session'] = Session(
                idp=kwargs.pop("endpoint", DEFAULT_IDP),
                username=kwargs.pop("username", None),
                password=kwargs.pop("password", None),
                kerberos=kwargs.pop("kerberos", None),
                cookiejar=kwargs.pop("cookiejar", None),
            )
        return func(*args, **kwargs)
    return _wrapper


def _session_func_factory(method, docstring):
    @_ecp_session
    def _func(url, **kwargs):
        # the decorator guarantees us a session
        with kwargs.pop("session") as session:
            meth = getattr(session, method)
            return meth(url, **kwargs)
    _func.__doc__ = docstring + _request_params_doc.format(method=method)
    return _func


_request_params_doc = """
    Parameters
    ----------
    url : `str`
        URL path for request.

    endpoint : `str`, optional
        ECP endpoint name or URL for request.

    username : `str`, optional
        the username with which to authenticate, will be prompted for
        if not given, and not using ``kerberos``.

    password : `str`, optional
        the password with which to authenticate, will be prompted for
        if not given, and not using ``kerberos``.

    kerberos : `bool`, optional
        use existing kerberos credential for login, default is to try, but
        fall back to username/password prompt.

    cookiejar : `http.cookiejar.CookieJar`, optional
        a jar of cookies to add to the `requests.Session`.

    kwargs
        other keyword arguments are passed directly to
        :meth:`requests.Session.{method}`

    Returns
    -------
    response : `http.client.HTTPResponse`
        the response from the URL

    See Also
    --------
    requests.Session.{method}
        for full details of the request handling
"""

get = _session_func_factory(
    "get",
    """Send a GET request using ECP authentication
    """
)

request = _session_func_factory(
    "request",
    """Request a URL using ECP authentication
    """
)
