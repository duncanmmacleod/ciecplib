##########
 ciecplib
##########

The `ciecplib` python client provides a functions and command-line utilities to
authenticate against SAML/ECP endpoints, and retrieve URLs from behind that
authentication.

============
Installation
============

.. tabs::

   .. tab:: Pip

      .. code-block:: bash

          $ python -m pip install ciecplib

      Supported python versions: 3.5+.

      .. admonition:: Default ``pip install`` doesn't include Kerberos Auth support

          By default ``pip install ciecplib`` does not bundle
          Kerberos auth support that is optional as of requests-ecp 0.3.0.

          The ``ciecplib[kerberos]`` extra can be used to automatically
          install ``requests-ecp[kerberos]``:

          .. code-block:: shell

              python -m pip install ciecplib[kerberos]

          This does not ensure that a working version of the underlying GSSAPI
          is installed (e.g, via MIT Kerberos).
          If you need Kerberos auth, and need to install GSSAPI itself on your
          system, it is recommended that you
          **use Conda to install `ciecplib`**.

   .. tab:: Conda

      .. code-block:: bash

          $ conda install -c conda-forge ciecplib

      Supported python versions: 3.6+.

==================
User documentation
==================

.. automodapi:: ciecplib
   :no-inheritance-diagram:
   :no-main-docstr:
   :headings: =-

API
===

.. toctree::

   api/ciecplib

|

Command-line scripts
====================

.. toctree::
   :maxdepth: 1

   ecp-cert-info
   ecp-curl
   ecp-get-cert
   ecp-get-cookie

|

==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
