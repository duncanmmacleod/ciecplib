##########
 LIGO.ORG
##########

The LIGO.ORG python client provides a functions and command-line utilities to
authenticate against SAML/ECP endpoints, and retrieve URLs from behind LIGO.ORG
authentication.

============
Installation
============

.. tabs::

   .. tab:: Pip

      .. code-block:: bash

          $ python -m pip install ligo.org

      Supported python versions: 2.7, 3.4+.

   .. tab:: Conda

      .. code-block:: bash

          $ conda install -c conda-forge ligo.org

      Supported python versions: 2.7, 3.6+.

   .. tab:: Debian Linux

      .. code-block:: bash

          $ apt-get install python-ligo-org

      Supported python versions: 2.7,
      `click here for instructions on how to add the required debian repositories
      <https://wiki.ligo.org/Computing/Debian>`__.

   .. tab:: Scientific Linux

      .. code-block:: bash

          $ yum install python2-ligo-org

      Supported python versions: 2.7,
      `click here for instructions on how to add the required yum repositories
      <https://wiki.ligo.org/Computing/ScientificLinux7>`__.

==================
User documentation
==================

.. automodapi:: ligo.org
   :no-inheritance-diagram:
   :no-main-docstr:
   :headings: =-

API
===

.. toctree::

   api/ligo.org

|

Command-line scripts
====================

.. toctree::
   :maxdepth: 1

   ligo-proxy-init
   ligo-curl

|

==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
