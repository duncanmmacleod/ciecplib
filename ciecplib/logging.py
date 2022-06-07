# -*- coding: utf-8 -*-
# Copyright (C) Cardiff University (2022)
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

"""Logging utilities for CIECPLib
"""

import logging
from http.client import HTTPConnection

logging.basicConfig()
ROOT_LOGGER = logging.getLogger()
URLLIB3_LOGGER = logging.getLogger("requests.packages.urllib3")
LOGGERS = (
    ROOT_LOGGER,
    URLLIB3_LOGGER,
)
_DEFAULT_LEVEL = {logger: logger.level for logger in LOGGERS}


def init_logging(level=logging.DEBUG):
    """Enable logging in requests.

    This function is taken from
    https://requests.readthedocs.io/en/v2.9.1/api/#api-changes
    """
    if level is None:  # restore to default
        level = _DEFAULT_LEVEL
    else:
        level = {logger: level for logger in LOGGERS}
    # set level
    for logger in LOGGERS:
        logger.setLevel(level[logger])
    # set debug logging for connections
    debug = ROOT_LOGGER.isEnabledFor(logging.DEBUG)
    HTTPConnection.debuglevel = int(debug)
    URLLIB3_LOGGER.propagate = debug
    return URLLIB3_LOGGER


def reset_logging():
    """Reset the logging levels back to their original values.
    """
    return init_logging(level=None)
