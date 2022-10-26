*********************
Code Style Guidelines
*********************


.. _black-code-style:

Black
-----

We use the `black <https://github.com/psf/black>`_ coding style, a flavour of `PEP-8 <https://www.python.org/dev/peps/pep-0008/>`_ for Python.

We use a `pre-commit-hook <https://pre-commit.com/>`_ to apply this style before committing, so you don't have to bother about formatting.
Just code how you feel comfortable and let the tool do the work for you (see :ref:`pre-commit-hooks`).

If you want to apply the formatting without committing, use our developer tool :github-source:`dev-tools/black.sh`::

    ./dev-tools/black.sh


.. _djlint:

DjLint
------

We use `djlint <https://www.djlint.com/>`__ to format our Django HTML templates.

We use a `pre-commit-hook <https://pre-commit.com/>`_ to apply this style before committing, so you don't have to bother about formatting.
Just code how you feel comfortable and let the tool do the work for you (see :ref:`pre-commit-hooks`).

If you want to apply the formatting without committing, use our developer tool :github-source:`dev-tools/djlint.sh`::

    ./dev-tools/djlint.sh


.. _prettier-code-style:

Prettier
--------

We use `prettier <https://prettier.io/>`_ to format our static JS and CSS files.

We use a `pre-commit-hook <https://pre-commit.com/>`_ to apply this style before committing, so you don't have to bother about formatting.
Just code how you feel comfortable and let the tool do the work for you (see :ref:`pre-commit-hooks`).

If you want to apply the formatting without committing, use our developer tool :github-source:`dev-tools/prettier.sh`::

    ./dev-tools/prettier.sh


.. _pylint:

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


.. _shellcheck:

Shellcheck
----------

All developer tools in the :github-source:`dev-tools` directory have to comply to the standards of shellcheck (see
`ShellCheck wiki <https://github.com/koalaman/shellcheck/wiki>`_).
Shellcheck is run both in the CI-pipeline of CircleCI (see :ref:`circleci-shellcheck`) and as pre-commit hook (see
:ref:`pre-commit-hooks`) and can be run locally with::

    shellcheck -x dev-tools/*

False positives can be `ignored <https://github.com/koalaman/shellcheck/wiki/Ignore>`_ with the syntax::

    # shellcheck disable=SC2059
