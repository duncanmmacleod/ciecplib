# LIGO.ORG for Python

This small python package provides a native Python client to access LIGO.ORG-authenticated web content.

The core of this package was written by Scott Koranda, while the rest of the package is maintained by [Duncan Macleod](//github.com/duncanmmacleod).

This packages uses an existing Kerberos ticket to authenticate against the LIGO.ORG SAML service.

Assuming a Kerberos ticket has been created via

```bash
kinit albert.einstein@LIGO.ORG
```

the basic usage is as follows

```python
from ligo.org import request
response = request('https://somewhere.ligo.org/mywebpage/')
```

The `response` is then a file-like object from which data can be read.
