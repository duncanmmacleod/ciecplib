# LIGO.ORG for Python

This small python package provides a native Python client to access LIGO.ORG-authenticated web content.

The core of this package was written by Scott Koranda, while the rest of the package is maintained by [Duncan Macleod](//github.com/duncanmmacleod).

This packages uses an existing Kerberos ticket to authenticate against the LIGO.ORG SAML service.

## Development status

[![Linux](https://img.shields.io/circleci/project/github/duncanmmacleod/ligo.org/master.svg?label=Linux)](https://circleci.com/gh/duncanmmacleod/ligo.org)
[![Windows](https://img.shields.io/appveyor/ci/duncanmmacleod/ligo-org/master.svg?label=Windows)](https://ci.appveyor.com/project/duncanmmacleod/ligo-org/branch/master)
[![codecov](https://codecov.io/gh/duncanmmacleod/ligo.org/branch/master/graph/badge.svg)](https://codecov.io/gh/duncanmmacleod/ligo.org)
[![Maintainability](https://api.codeclimate.com/v1/badges/2cf14445b3e070133745/maintainability)](https://codeclimate.com/github/duncanmmacleod/ligo.org/maintainability)

## Installation

You can install the package via

```bash
pip install git+https://github.com/duncanmmacleod/ligo.org.git
```

## Basic usage

```python
>>> from ligo.org import request
>>> response = request('https://somewhere.ligo.org/mywebpage/')
```
