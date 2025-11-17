Docstrings
==========

Sphinx
------

In the python files please add docstrings in the sphinx format (see :doc:`sphinx-rtd-tutorial:docstrings`)::

    """
    [Summary]

    :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
    ...

    :return: [ReturnDescription]

    :raises [ErrorType]: [ErrorDescription]
    ...
    """


.. Hint::

    In the model documentation, the parameters are not required, because they are automatically derived from the
    model field type.

Whenever you want to document module/class attributes which are not parameters (i.e. because they are not passed to the
``__init__()``-function or contain static values), use inline comments::

    #: Description of attribute
    attribute = "value of this attribute"

See the configuration files :mod:`~integreat_cms.core.settings` and :mod:`conf` or :mod:`~integreat_cms.cms.constants` for examples.


Typedoc
-------

In the static TypeScript files, please add docstrings **directly before the export** you want to comment on.  
If you want to write a docstring for the module itself (not attached to a specific export), add the ``@module`` tag inside the docstring.

Example for an export:

.. code-block:: typescript

    /**
     * docs for example
     */
    export const example = () => {}

Example for a module docstring:

.. code-block:: typescript

    /**
     * Some comment about the module
     * @module name-of-module
     */

For more information on how to use docstrings, please refer to the `TypeDoc documentation <https://typedoc.org/modules.html>`_.
