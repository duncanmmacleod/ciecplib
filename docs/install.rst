.. _ciecplib-install:

###################
Installing CIECPLib
###################

.. _ciecplib-install-conda:

=====
Conda
=====

.. code-block:: bash
    :name: ciecplib-install-conda-code
    :caption: Installing CIECPLib with Conda

    conda install -c conda-forge ciecplib


.. _ciecplib-install-pip:

===
Pip
===

.. code-block:: bash
    :name: ciecplib-install-pip-code
    :caption: Installing CIECPLib with Pip

    $ python -m pip install ciecplib

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


