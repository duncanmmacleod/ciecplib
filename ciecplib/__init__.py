# Copyright (C) 2019-2025 Cardiff University
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

"""CIECPLib provides a Python library and command-line utilities
to make HTTP requests with SAML/ECP authentication.

This allows requesting documents from behind SAML/Shibboleth
authentication systems.
"""

# request the contents of a URL
from .requests import (
    get,
    head,
    post,
)

# generate session handling
from .sessions import Session

# user interfaces
from .ui import (
    get_cert,
    get_cookie,
)

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"
__credits__ = "Scott Koranda, Dave Dykstra"
__version__ = "0.8.2"
