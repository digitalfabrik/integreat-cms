****************************
Virtual Environment (Pipenv)
****************************

All python dependencies are installed in a virtual Python environment (see :doc:`tutorial/venv`).

As package manager for the virtual environment we use Pipenv

For portability and reproducibility, we use specific version of our dependencies locked in :github-source:`Pipfile.lock`.


Install dependencies
====================

To install exactly the specified versions of the dependencies, execute::

    pipenv install --dev

.. Note::

    This is also part of the ``install.sh`` dev-tool.


Add dependencies
================

When adding new functional dependencies, please add them to :github-source:`setup.cfg` and execute::

    pipenv install --dev

When adding a new dev dependency ``package``, just use::

    pipenv install --dev package


Update dependencies
===================

When you want to update the locked versions of the dependencies, execute::

    pipenv update

.. Note::
    This is also part of the ``update_dependencies.sh`` dev-tool.


Remove virtual environment
==========================

When you want to remove the virtual environment together with all installed dependencies, execute::

    pipenv --rm
