*******************
Virtual Environment
*******************

All python dependencies are installed in a virtual Python environment (see :doc:`python:tutorial/venv`).

For portability and reproducibility, the exact versions of all dependencies (including transitive
ones) are locked in :github-source:`uv.lock`, which is managed by `uv <https://docs.astral.sh/uv/>`_.


Install dependencies
====================

To install exactly the versions from the lock file, execute::

    uv sync --locked

.. Note::

    This is also part of the ``install.sh`` dev-tool. It creates the ``.venv`` directory if it does
    not exist yet, using a Python interpreter which satisfies the ``requires-python`` constraint of
    :github-source:`pyproject.toml`.


Add dependencies
================

Adding dependencies differs based on whether they are functional or only needed in development.
In both cases, ``uv`` adds the package to :github-source:`pyproject.toml`, updates
:github-source:`uv.lock` and installs it in the venv in one step.

Production dependencies
-----------------------

Added to the ``[project].dependencies`` section::

    uv add <package>

Development dependencies
------------------------

Added to the ``[dependency-groups].dev`` section::

    uv add --dev <package>

.. Note::

    Both :github-source:`uv.lock` and :github-source:`pyproject.toml` have to be committed together,
    otherwise the ``uv-install`` job of the :doc:`continuous-integration` fails.


Update dependencies
===================

When you want to update the locked versions of the dependencies,
use the developer tool :github-source:`tools/update_dependencies.sh`::

    ./tools/update_dependencies.sh

To update a single package instead of all of them, e.g. to apply a security fix without pulling in
unrelated changes, pass its name::

    ./tools/update_dependencies.sh --package django


Remove virtual environment
==========================

When you want to remove the virtual environment together with all installed dependencies, execute::

    rm -rf .venv
