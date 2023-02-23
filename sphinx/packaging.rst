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
    integreat-cms-cli compilemessages
    # Bundle static files
    npm run prod

2. Move the README to make sure to include the PyPI-README instead of the GitHub-README::

    mv integreat_cms/README.md .

3. After that, you can build the python package with :doc:`setuptools:index`::

    pip3 install --upgrade pip build twine
    python3 -m build

   Then, the built package can be found in ``./dist/``.

Publish package
===============

You can publish the package to a python repository like e.g. `PyPI <https://pypi.org/>`__ with :doc:`twine:index`::

    twine upload ./dist/integreat-cms-*.tar.gz

See the :doc:`Twine documentation <twine:index>` for all configuration options of this command.
