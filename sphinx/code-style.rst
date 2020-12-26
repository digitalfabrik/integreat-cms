*********************
Code Style Guidelines
*********************


Black
-----

We use the `black <https://github.com/psf/black>`_ coding style, a flavour of `PEP-8 <https://www.python.org/dev/peps/pep-0008/>`_ for Python.

We use a `pre-commit-hook <https://pre-commit.com/>`_ to apply this style before committing, so you don't have to bother about formatting.
Just code how you feel comfortable and let the tool do the work for you.

If you want to apply the code without committing, use our developer tool :github-source:`dev-tools/black.sh`::
::

    ./dev-tools/black.sh


Linting
-------

In addition to black, we use pylint to check the code for semantic correctness.
Run pylint with our developer tool :github-source:`dev-tools/pylint.sh`::

    ./dev-tools/pylint.sh

When you think a warning is a false positive, add a comment before the specific line::

    # pylint: disable=unused-argument
    def some_function(*args, **kwargs)

.. Note::

    Please use the string identifiers (``unused-argument``) instead of the alphanumeric code (``W0613``) when disabling warnings.

.. Hint::

    If you want to run both tools at once, use our developer tool :github-source:`dev-tools/code_style.sh`::

        ./dev-tools/code_style.sh

.. include:: _docstrings.rst
