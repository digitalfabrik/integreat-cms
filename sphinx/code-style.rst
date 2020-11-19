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

Docstrings
----------

Please add docstrings in the sphinx format (see :doc:`sphinx-rtd-tutorial:docstrings`)::

    """
    [Summary]

    :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
    :type [ParamName]: [ParamType](, optional)
    ...

    :raises [ErrorType]: [ErrorDescription]
    ...

    :return: [ReturnDescription]
    :rtype: [ReturnType]
    """


.. Note::

    Please use the correct Python :doc:`python:library/datatypes` (e.g. ``str`` instead of ``string``, ``int`` instead
    of ``integer``) and provide absolute paths to any referenced classes (e.g. ``~cms.models.regions.region.Region``).
    If the module path is very long or doesn't add much information, consider using a tilde ``~`` as prefix to show only
    the class name.

.. Hint::

    In the model documentation, the parameter types are not required, because they are automatically derived from the
    model field type. See :func:`~conf.process_django_models` for more information.
