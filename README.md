# CI ECP for Python

This python package provides a native Python client to access SAML/ECP authenticated content over HTTP.

## Development status

[![Linux](https://img.shields.io/circleci/project/github/duncanmmacleod/ciecplib/master.svg?label=Linux)](https://circleci.com/gh/duncanmmacleod/ciecplib)
[![Windows](https://img.shields.io/appveyor/ci/duncanmmacleod/ciecplib/master.svg?label=Windows)](https://ci.appveyor.com/project/duncanmmacleod/ciecplib/branch/master)
[![codecov](https://codecov.io/gh/duncanmmacleod/ciecplib/branch/master/graph/badge.svg)](https://codecov.io/gh/duncanmmacleod/ciecplib)
[![Maintainability](https://api.codeclimate.com/v1/badges/2cf14445b3e070133745/maintainability)](https://codeclimate.com/github/duncanmmacleod/ciecplib/maintainability)

## Installation

You can install the package via

```bash
pip install git+https://github.com/duncanmmacleod/ciecplib.git
```

## Basic usage

```python
>>> from ciecplib import request
>>> response = request('https://somewhere.org/mywebpage/')
```
