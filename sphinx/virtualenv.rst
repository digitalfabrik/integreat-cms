*******************
Virtual Environment
*******************

All python dependencies are installed in a virtual Python environment (see :doc:`tutorial/venv`).

As package manager for the virtual environment we use Pipenv (see :doc:`pipenv:index`)

For portability and reproducibility, we use specific version of our dependencies locked in ``Pipenv.lock`` `[Source] <https://github.com/Integreat/cms-django/blob/develop/Pipfile.lock>`_.


Install dependencies
====================

To install exactly the specified versions of the dependencies, execute::

    pipenv install

.. Note::

    This is also part of the ``install.sh`` dev-tool.


Add dependencies
================

When adding new dependencies, please add them to ``setup.py`` and execute::

    pipenv install '-e .[dev]'


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
