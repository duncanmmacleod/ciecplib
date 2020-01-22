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

      Supported python versions: 2.7, 3.5+.

   .. tab:: Conda

      .. code-block:: bash

          $ conda install -c conda-forge ciecplib

      Supported python versions: 2.7, 3.6+.

   .. tab:: Debian Linux

      .. code-block:: bash

          $ apt-get install python3-ciecplib ciecp-utils

      Supported python versions: 2.7, 3.7

   .. tab:: Scientific Linux

      .. code-block:: bash

          $ yum install python2-ciecplib ciecp-utils

      Supported python versions: 2.7

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
   ecp-cookie-init
   ecp-curl
   ecp-get-cert

|

==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
