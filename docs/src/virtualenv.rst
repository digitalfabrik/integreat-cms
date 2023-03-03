*******************
Virtual Environment
*******************

All python dependencies are installed in a virtual Python environment (see :doc:`python:tutorial/venv`).

For portability and reproducibility, we use specific version of our dependencies locked in :github-source:`pyproject.toml`.


Install dependencies
====================

To install exactly the specified versions of the dependencies, execute::

    pip install -e .[dev,pinned]

.. Note::

    This is also part of the ``install.sh`` dev-tool.


Add dependencies
================

Adding dependencies differs based on whether they are functional or only needed in development.

Development dependencies
------------------------

1. Add the new package to the ``[project.optional-dependencies].dev`` section in :github-source:`pyproject.toml`
2. Execute :github-source:`tools/install.sh` to install it in the venv

Production dependencies
-----------------------

1. Add the new package to the ``[project].dependencies`` section in :github-source:`pyproject.toml`
2. Execute :github-source:`tools/update_dependencies.sh`, which should update the pinned versions
   in ``[project.optional-dependencies].pinned`` of :github-source:`pyproject.toml`.


Update dependencies
===================

When you want to update the locked versions of the production dependencies,
use the developer tool :github-source:`tools/update_dependencies.sh`::

    ./tools/update_dependencies.sh


Remove virtual environment
==========================

When you want to remove the virtual environment together with all installed dependencies, execute::

    rm -rf .venv
