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

3. Bundle the locked dependency versions into the package (see :ref:`bundled-lock-files`)::

    uv export --frozen --no-dev --no-emit-project --no-annotate \
        --format pylock.toml -o integreat_cms/pylock.toml
    uv export --frozen --no-dev --no-emit-project --no-annotate \
        --format requirements.txt -o integreat_cms/requirements.lock.txt

4. After that, you can build the python package with :doc:`setuptools:index`::

    python3 -m build

   Then, the built package can be found in ``./dist/``.


.. _bundled-lock-files:

Bundled lock files
==================

Every distribution contains the exact dependency versions the release was tested with, exported from
:github-source:`uv.lock`:

* ``integreat_cms/pylock.toml`` - the `PEP 751 <https://peps.python.org/pep-0751/>`__ lock format,
  including a ``sha256`` hash per package. Requires pip 26.1 or later.
* ``integreat_cms/requirements.lock.txt`` - the same set in the ``requirements.txt`` format, as a
  fallback for older pip versions.

These files do not constrain a regular ``pip install integreat-cms``, which keeps resolving the
dependencies as usual. They only take effect when a deployment explicitly passes them to pip, see
:ref:`Install pinned dependencies <prod-server-pinned-dependencies>`.

Publish package
===============

You can publish the package to a python repository like e.g. `PyPI <https://pypi.org/>`__ with :doc:`twine:index`::

    twine upload ./dist/integreat_cms-*.tar.gz

See the :doc:`Twine documentation <twine:index>` for all configuration options of this command.
