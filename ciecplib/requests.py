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

"""HTTP request method with end-to-end ECP authentication
"""

from functools import wraps
try:
    from contextlib import nullcontext
except ImportError:  # python < 3.7
    class nullcontext:
        def __init__(self, enter_result=None):
            self.enter_result = enter_result

        def __enter__(self):
            return self.enter_result

        def __exit__(self, *excinfo):
            pass

from .env import DEFAULT_IDP
from .sessions import Session

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"


def _ecp_session(func):
    """Decorate a function to open a `requests_ecp.Session`.

    If a `Session` is already open, this function returns an instance of
    `contextlib.nullcontext` that should _only_ be used with the `with`
    statement, not a real `Session` object. This is only to support chaining
    this method reentrant with respect to setting/resetting debug logging
    levels.
    """
    @wraps(func)
    def _wrapper(*args, **kwargs):
        sess = kwargs.pop("session", None)
        if sess is None:
            sess = Session(
                idp=kwargs.pop("endpoint", DEFAULT_IDP),
                username=kwargs.pop("username", None),
                password=kwargs.pop("password", None),
                kerberos=kwargs.pop("kerberos", None),
                cookiejar=kwargs.pop("cookiejar", None),
                debug=kwargs.get("debug", False),
            )
        else:
            sess = nullcontext(enter_result=sess)
        return func(*args, session=sess, **kwargs)
    return _wrapper


def _session_func_factory(method, docstring):
    @_ecp_session
    def _func(url, **kwargs):
        kwargs.pop("debug", None)  # not supported by requests functions
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
    """Send a GET request using ECP authentication.
    """
)

head = _session_func_factory(
    "head",
    """Send a HEAD request using ECP authentication.
    """
)

post = _session_func_factory(
    "post",
    """Send a POST request using ECP authentication.
    """
)
