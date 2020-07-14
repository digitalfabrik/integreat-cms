*********************
Code Style Guidelines
*********************


PEP-8
-----

We mostly follow the `PEP-8 <https://www.python.org/dev/peps/pep-0008/>`_ coding style for Python.

Some examples of our coding conventions:

* Indentation: 4 spaces
* Maximum line length: 160 characters
* Closing brackets are lined up under the first character of the line that starts the multiline construct::

        result = some_function_that_takes_arguments(
            some_argument,
            some_other_argument,
            yet_another_argument,
        )


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


Linting
-------

Check whether the code complies to our style guides with the linting tool ``pylint.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/pylint.sh>`__]::

    ./dev-tools/pylint.sh

When you think a warning is a false positive, add a comment before the specific line::

    # pylint: disable=unused-argument
    def some_function(*args, **kwargs)

.. Note::

    Please use the string identifiers (``unused-argument``) instead of the alphanumeric code (``W0613``) when disabling warnings.
