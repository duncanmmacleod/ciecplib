# CI ECP for Python

This python package provides a native Python client to access
SAML/ECP-authenticated content over HTTP with
[CILogon](https://cilogon.org).

## Release status

[![PyPI version](https://badge.fury.io/py/ciecplib.svg)](http://badge.fury.io/py/ciecplib)
[![Conda version](https://img.shields.io/conda/vn/conda-forge/ciecplib.svg)](https://anaconda.org/conda-forge/ciecplib/)  
[![DOI](https://zenodo.org/badge/33156275.svg)](https://zenodo.org/badge/latestdoi/33156275)
[![License](https://img.shields.io/pypi/l/ciecplib.svg)](https://choosealicense.com/licenses/gpl-3.0/)
![Supported Python versions](https://img.shields.io/pypi/pyversions/ciecplib.svg)

## Development status

[![Travis](https://img.shields.io/travis/com/duncanmmacleod/ciecplib/master?label=Unix%20%28conda%29&logo=travis)](https://travis-ci.com/duncanmmacleod/ciecplib)
[![Circle](https://img.shields.io/circleci/project/github/duncanmmacleod/ciecplib/master.svg?label=Linux%20%28other%29&logo=circleci)](https://circleci.com/gh/duncanmmacleod/ciecplib)
[![Appveyor](https://img.shields.io/appveyor/ci/duncanmmacleod/ciecplib/master.svg?label=Windows%20%28conda%29&logo=appveyor)](https://ci.appveyor.com/project/duncanmmacleod/ciecplib/branch/master)  
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
