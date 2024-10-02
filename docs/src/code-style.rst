*********************
Code Style Guidelines
*********************


.. _black-code-style:

Black
-----

We use the `black <https://github.com/psf/black>`_ coding style, a flavour of `PEP-8 <https://www.python.org/dev/peps/pep-0008/>`_ for Python.

We use a `pre-commit-hook <https://pre-commit.com/>`_ to apply this style before committing, so you don't have to bother about formatting.
Just code how you feel comfortable and let the tool do the work for you (see :ref:`pre-commit-hooks`).

If you want to apply the formatting without committing, use our developer tool :github-source:`tools/black.sh`::

    ./tools/black.sh


.. _djlint:

DjLint
------

We use `djlint <https://www.djlint.com/>`__ to format our Django HTML templates.

We use a `pre-commit-hook <https://pre-commit.com/>`_ to apply this style before committing, so you don't have to bother about formatting.
Just code how you feel comfortable and let the tool do the work for you (see :ref:`pre-commit-hooks`).

If you want to apply the formatting without committing, use our developer tool :github-source:`tools/djlint.sh`::

    ./tools/djlint.sh


.. _prettier-code-style:

Prettier
--------

We use `prettier <https://prettier.io/>`_ to format our static JS and CSS files.

We use a `pre-commit-hook <https://pre-commit.com/>`_ to apply this style before committing, so you don't have to bother about formatting.
Just code how you feel comfortable and let the tool do the work for you (see :ref:`pre-commit-hooks`).

If you want to apply the formatting without committing, use our developer tool :github-source:`tools/prettier.sh`::

    ./tools/prettier.sh


.. _pylint:

Linting
-------

In addition to black, we use pylint to check the code for semantic correctness.
Run pylint with our developer tool :github-source:`tools/pylint.sh`::

    ./tools/pylint.sh

When you think a warning is a false positive, add a comment before the specific line::

    # pylint: disable=unused-argument
    def some_function(*args, **kwargs)

.. Note::

    Please use the string identifiers (``unused-argument``) instead of the alphanumeric code (``W0613``) when disabling warnings.

.. Hint::

    If you want to run both tools at once, use our developer tool :github-source:`tools/code_style.sh`::

        ./tools/code_style.sh

.. include:: _docstrings.rst


.. _mypy:

my[py]
------

We use `my[py] <https://mypy.readthedocs.io/en/stable/>`_ to check type annotations of our python code.

We use a `pre-commit-hook <https://pre-commit.com/>`_ to apply this check before committing, so TypeErrors will be prevented.
Just code how you feel comfortable and let the tool do the work for you (see :ref:`pre-commit-hooks`).

If you want to apply the formatting without committing, use our developer tool :github-source:`tools/mypy.sh`::

    ./tools/mypy.sh

.. Note::

    If you're unsure about a type, temporarily add ``reveal_type(variable)`` to the code and run ``./tools/mypy.sh``, the tool will then tell you what type it would guess.

    Any imports that are only needed during type checking should be wrapped into a ``if TYPE_CHECKING:`` block. For that the variable ``TYPE_CHECKING`` should be imported from ``typing``.

    The line ``from __future__ import annotations`` must be the first line (after the module docstring) of any new python file.
    (This activates PEP 563 for any python version where it is not already active by default, so we need to keep this until all python versions we support implement it. At the time of writing the first python version where this is not just optional is `still mentioned as TBD <https://docs.python.org/3/library/__future__.html#module-contents>`_)

    If a third party library is incorrectly typed or missing type hints, and this results in errors you cannot fix, then you can add ``# type: ignore[<error-class>]`` (where the ``<error-class>`` is the identifier of the error you're experiencing, e.g. ``attr-defined``) in the end of the line where the error is thrown.


.. _shellcheck:

Shellcheck
----------

All developer tools in the :github-source:`tools` directory have to comply to the standards of shellcheck (see
`ShellCheck wiki <https://github.com/koalaman/shellcheck/wiki>`_).
Shellcheck is run both in the CI-pipeline of CircleCI (see :ref:`circleci-shellcheck`) and as pre-commit hook (see
:ref:`pre-commit-hooks`) and can be run locally with::

    shellcheck -x tools/*

False positives can be `ignored <https://github.com/koalaman/shellcheck/wiki/Ignore>`_ with the syntax::

    # shellcheck disable=SC2059
