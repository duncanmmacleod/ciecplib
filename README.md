# CI ECP for Python

This python package provides a native Python client to access
SAML/ECP-authenticated content over HTTP with
[CILogon](https://cilogon.org).

## Release status

[![PyPI version](https://badge.fury.io/py/ciecplib.svg)](http://badge.fury.io/py/ciecplib)
[![Conda version](https://img.shields.io/conda/vn/conda-forge/ciecplib.svg)](https://anaconda.org/conda-forge/ciecplib/)

[![License](https://img.shields.io/pypi/l/ciecplib.svg)](https://choosealicense.com/licenses/gpl-3.0/)
![Supported Python versions](https://img.shields.io/pypi/pyversions/ciecplib.svg)

## Development status

[![Linux](https://img.shields.io/circleci/project/github/duncanmmacleod/ciecplib/master.svg?label=Linux)](https://circleci.com/gh/duncanmmacleod/ciecplib)
[![Windows](https://img.shields.io/appveyor/ci/duncanmmacleod/ciecplib/master.svg?label=Windows)](https://ci.appveyor.com/project/duncanmmacleod/ciecplib/branch/master)
[![codecov](https://codecov.io/gh/duncanmmacleod/ciecplib/branch/master/graph/badge.svg)](https://codecov.io/gh/duncanmmacleod/ciecplib)
[![Maintainability](https://api.codeclimate.com/v1/badges/2cf14445b3e070133745/maintainability)](https://codeclimate.com/github/duncanmmacleod/ciecplib/maintainability)
[![Documentation](https://readthedocs.org/projects/ciecplib/badge/?version=latest)](https://ciecplib.readthedocs.io/en/latest/?badge=latest)

## Installation

See https://ciecplib.readthedocs.io/en/latest/#installation for installation instructions.

## Basic usage

```python
>>> from ciecplib import request
>>> response = request('https://somewhere.org/mywebpage/')
```
