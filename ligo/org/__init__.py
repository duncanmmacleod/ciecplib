# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2013)
#
# This file is part of LIGO.ORG.
#
# LIGO.ORG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LIGO.ORG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LIGO.ORG.  If not, see <http://www.gnu.org/licenses/>.

"""This module provides LIGO.ORG authenticated HTML queries
"""

from . import version

from .ecp import *
from .kerberos import *
from ._version import get_versions

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Scott Koranda <scott.koranda@ligo.org>'
__version__ = get_versions()['version']

del get_versions
