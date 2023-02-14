# CI ECP for Python

This python package provides a native Python client to access
SAML/ECP-authenticated content over HTTP with
[CILogon](https://cilogon.org).

## Release status

[![PyPI version](https://img.shields.io/pypi/v/ciecplib.svg)](https://pypi.python.org/pypi/ciecplib)
[![Conda version](https://img.shields.io/conda/vn/conda-forge/ciecplib.svg)](https://anaconda.org/conda-forge/ciecplib/)  
[![DOI](https://zenodo.org/badge/33156275.svg)](https://zenodo.org/badge/latestdoi/33156275)
[![License](https://img.shields.io/pypi/l/ciecplib.svg)](https://choosealicense.com/licenses/gpl-3.0/)
![Supported Python versions](https://img.shields.io/pypi/pyversions/ciecplib.svg)

## Development status

[![Build status](https://github.com/duncanmmacleod/ciecplib/actions/workflows/python.yml/badge.svg?branch=main)](https://github.com/duncanmmacleod/ciecplib/actions/workflows/python.yml)
[![Codecov](https://img.shields.io/codecov/c/gh/duncanmmacleod/ciecplib?logo=codecov)](https://codecov.io/gh/duncanmmacleod/ciecplib)
[![Maintainability](https://api.codeclimate.com/v1/badges/9e777f5fe160d1e3e7b6/maintainability)](https://codeclimate.com/github/duncanmmacleod/ciecplib/maintainability)
[![Documentation](https://readthedocs.org/projects/ciecplib/badge/?version=latest)](https://ciecplib.readthedocs.io/en/latest/?badge=latest)

## Installation

See https://ciecplib.readthedocs.io/en/latest/#installation for installation instructions.

## Basic usage

```python
>>> from ciecplib import request
>>> response = request('https://somewhere.org/mywebpage/')
```
