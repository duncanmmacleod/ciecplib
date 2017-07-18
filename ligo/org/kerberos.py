# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2013)
#
# This file is part of GWpy.
#
# GWpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWpy.  If not, see <http://www.gnu.org/licenses/>.

"""LIGO.ORG utility module to initialise a kerberos ticket

This module provides a lazy-mans python version of the 'kinit'
command-line tool, with internal guesswork using keytabs

See the documentation of the `kinit` function for example usage
"""

import getpass
import os
import sys
import re
from subprocess import (PIPE, Popen)

from six.moves import http_cookiejar, input

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"
__all__ = ['kinit', 'klist']

KLIST_REGEX = re.compile(r"(?P<start>\d\d/\d\d/\d\d\d\d\s\d\d:\d\d:\d\d)\s+"
                         r"(?P<expiry>\d\d/\d\d/\d\d\d\d\s\d\d:\d\d:\d\d)\s+"
                         r"(?P<principal>(.*)$)")


class KerberosError(RuntimeError):
    pass


def which(program):
    """Find full path of executable program

    Parameters
    ----------
    program : `str`
        path of executable name for which to search

    Returns
    -------
    programpath
        the full absolute path of the executable

    Raises
    ------
    ValueError
        if not executable program is found
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    raise ValueError("No executable '%s' found in PATH" % program)


def kinit(username=None, password=None, realm=None, exe=None, keytab=None,
          krb5ccname=None, verbose=False):
    """Initialise a kerberos (krb5) ticket.

    This allows authenticated connections to, amongst others, NDS2
    services.

    Parameters
    ----------
    username : `str`, optional
        name of user, will be prompted for if not given
    password : `str`, optional
        cleartext password of user for given realm, will be prompted for
        if not given
    realm : `str`
        name of realm to authenticate against, defaults to 'LIGO.ORG'
        if not given or parsed from the keytab
    exe : `str`
        path to kinit executable
    keytab : `str`
        path to keytab file. If not given this will be read from the
        ``KRB5_KTNAME`` environment variable. See notes for more details

    Notes
    -----
    If a keytab is given, or is read from the KRB5_KTNAME environment
    variable, this will be used to guess the username and realm, if it
    contains only a single credential

    Examples
    --------
    Example 1: standard user input, with password prompt::

        >>> from ligo.org import kinit
        >>> kinit('albert.einstein')
        Password for albert.einstein@LIGO.ORG:
        Kerberos ticket generated for albert.einstein@LIGO.ORG

    Example 2: extract username and realm from keytab, and use that
    in authentication::

        >>> kinit(keytab='~/.kerberos/ligo.org.keytab')
        Kerberos ticket generated for albert.einstein@LIGO.ORG
    """
    # get kinit path and user keytab
    if exe is None:
        exe = which('kinit')
    if keytab is None:
        keytab = os.environ.get('KRB5_KTNAME', None)
        if keytab is None or not os.path.isfile(keytab):
            keytab = None
    if keytab:
        try:
            principals = parse_keytab(keytab)
        except KerberosError:
            pass
        else:
            # is there's only one entry in the keytab, use that
            if username is None and len(principals) == 1:
                username = principals[0][0]
            # or if the given username is in the keytab, find the realm
            if username in list(zip(*principals))[0]:
                idx = list(zip(*principals))[0].index(username)
                realm = principals[idx][1]
            # otherwise this keytab is useless, so remove it
            else:
                keytab = None
    if realm is None:
        realm = 'LIGO.ORG'
    if username is None:
        verbose = True
        username = input("Please provide username for the %s kerberos "
                             "realm: " % realm)
    if not keytab and password is None:
        verbose = True
        password = getpass.getpass(
            prompt="Password for %s@%s: " % (username, realm),
            stream=sys.stdout)
    if keytab:
        cmd = [exe, '-k', '-t', keytab, '%s@%s' % (username, realm)]
    else:
        cmd = [exe, '%s@%s' % (username, realm)]
    if krb5ccname:
        krbenv = {'KRB5CCNAME': krb5ccname}
    else:
        krbenv = None

    kget = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE, env=krbenv)
    if not keytab:
        kget.communicate(password)
    kget.wait()
    if verbose:
        print("Kerberos ticket generated for %s@%s" % (username, realm))


def klist():
    """Run ``klist`` to get list of kerberos principals

    Parameters
    ----------
    keytab : `str`
        path to keytab file
    """
    # run klist to get list of principals
    klist_ = Popen(['klist'], stdout=PIPE, stderr=PIPE)
    out, err = klist_.communicate()
    if klist_.returncode:
        raise KerberosError(err)

    # parse list of principals
    principals = []
    for line in out.splitlines():
        try:
            principals.append(
                KLIST_REGEX.match(line.decode('utf-8')
                ).groupdict()['principal'])
        except AttributeError:
            continue
    return principals


def parse_keytab(keytab):
    """Read service principals from a keytab file

    Parameters
    ----------
    keytab : `str`
        path to keytab file
    """
    cmd = ['klist', '-k', '-K', keytab]
    klist_ = Popen(cmd, stdout=PIPE, stderr=PIPE)
    out, err = klist_.communicate()
    if klist_.returncode:
        raise KerberosError(err)
    principals = []
    for line in out.splitlines():
        try:
            n, principal, _ = line.decode('utf-8').split(None, 2)
        except ValueError:
            continue
        else:
            if not n.isdigit():
                continue
            principals.append(principal.split('@'))
    return principals
