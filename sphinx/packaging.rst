*********
Packaging
*********

.. highlight:: bash


Create python package
=====================

Packaging for a Python repository like e.g. `PyPI <https://pypi.org/>`__ is automated via our
:doc:`continuous-integration` (see :ref:`circleci-build-package`). If you want to do the packaging process manually, follow these steps:

1. Build all static files which are required::

    # Compile translation file
    pipenv run integreat-cms-cli compilemessages
    # Bundle static files
    npm run prod

2. After that, you can build the python package with :doc:`setuptools:index`::

    pip3 install --upgrade pip setuptools wheel
    python3 setup.py sdist bdist_wheel

   Then, the built package can be found in ``./dist/``.

Publish package
===============

You can publish the package to a python repository like e.g. `PyPI <https://pypi.org/>`__ with :doc:`twine:index`::

    pipenv run twine upload ./dist/integreat-cms-*.tar.gz

See the :doc:`Twine documentation <twine:index>` for all configuration options of this command.
