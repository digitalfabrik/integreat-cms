"""
Configuration file for the Sphinx documentation builder.

This file only contains the options which deviate from the default values.
For a full list see the documentation: :doc:`sphinx:usage/configuration`
"""

# -- Path setup --------------------------------------------------------------

import os
import sys
import inspect
import importlib
import django

from backend.settings import VERSION

# Append project source directory to path environment variable
sys.path.append(os.path.abspath("../src/"))
# Append sphinx source directory to path environment variable to allow documentation for this file
sys.path.append(os.path.abspath("./"))
os.environ["DJANGO_SETTINGS_MODULE"] = "backend.settings"


# Setup Django
django.setup()


def setup(app):
    """
    This method performs the initial setup for this sphinx configuration.
    It connects the function :func:`process_django_models` to the :event:`sphinx:autodoc-process-docstring` event.
    Furthermore, it registers the custom text role ``:event:`` to allow intersphinx mappings to e.g. :ref:`sphinx:events`.

    :param app: The sphinx application object
    :type app: ~sphinx.application.Sphinx
    """
    # Register the docstring processor with sphinx to improve the appearance of Django models
    app.connect("autodoc-process-docstring", process_django_models)
    # Allow the usage of the custom :event: text role in intersphinx mappings
    app.add_object_type("event", "event")


# -- Project information -----------------------------------------------------

#: The project name
project = "integreat-cms"
# pylint: disable=redefined-builtin
#: The copyright notice
copyright = "2020, Integreat"
#: The project author
author = "Integreat"

#: The full version, including alpha/beta/rc tags
release = VERSION

# -- General configuration ---------------------------------------------------

#: All enabled sphinx extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "sphinxcontrib_django",
    "sphinx_rtd_theme",
    "sphinx_last_updated_by_git",
    "sphinx_js",
]
#: Enable cross-references to other documentations
intersphinx_mapping = {
    "python": ("https://docs.python.org/3.7", None),
    "pipenv": ("https://pipenv.pypa.io/en/latest/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
    "sphinx-rtd-theme": (
        "https://sphinx-rtd-theme.readthedocs.io/en/latest/",
        None,
    ),
    "sphinx-rtd-tutorial": (
        "https://sphinx-rtd-tutorial.readthedocs.io/en/latest/",
        None,
    ),
    "django": (
        "https://docs.djangoproject.com/en/2.2/",
        "https://docs.djangoproject.com/en/2.2/_objects/",
    ),
    "django-mptt": ("https://django-mptt.readthedocs.io/en/latest/", None),
    "wsgi": ("https://wsgi.readthedocs.io/en/latest/", None),
    "xhtml2pdf": ("https://xhtml2pdf.readthedocs.io/en/latest", None),
}


#: The path for patched template files
templates_path = ["templates"]

# -- Options for HTML output -------------------------------------------------

#: The theme to use for HTML and HTML Help pages.
html_theme = "sphinx_rtd_theme"
#: Do not show the project name, only the logo
html_theme_options = {
    "logo_only": False,
    "collapse_navigation": False,
}
#: The logo shown in the menu bar
html_logo = "../src/cms/static/images/integreat-logo-white.png"
#: The facivon of the html doc files
html_favicon = "../src/cms/static/images/favicon.ico"
#: The url where the docs should be published (via gh-pages)
html_baseurl = "https://Integreat.github.io/cms-django/"
#: Do not include links to the documentation source (.rst files) in build
html_show_sourcelink = False
#: Do not include a link to sphinx
html_show_sphinx = False
#: Include last updated timestamp
html_last_updated_fmt = "%b %d, %Y"

# -- Settings for sphinx-js

#: Path to javascript files
js_source_path = "../src/cms/static/js"

# -- Modify default Django model parameter types------------------------------


# pylint: disable=unused-argument, too-many-locals, too-many-branches
def process_django_models(app, what, name, obj, options, lines):
    """
    This function is executed when sphinx emits the :event:`sphinx:autodoc-process-docstring` event.
    Even though it gets invoked on all objects which have docstrings, it only modifies the docstrings of Django models.
    It allows to omit parameter types in model docstrings and determines the correct types from the model fields.
    It is an improvement of the function `_add_model_fields_as_params() <https://github.com/edoburu/sphinxcontrib-django/blob/5417a320aedb9d6eb76ba1d076a9b9aa2eb3801e/sphinxcontrib_django/docstrings.py#L122>`__
    of the `sphinxcontrib-django <https://pypi.org/project/sphinxcontrib-django/>`__ extension.

    :param app: The sphinx application object
    :type app: ~sphinx.application.Sphinx

    :param what: The type of the object which the docstring belongs to (one of ``module``, ``class``, ``exception``,
                 ``function``, ``method`` and ``attribute``)
    :type what: str

    :param name: The fully qualified name of the object
    :type name: str

    :param obj: The documented object
    :type obj: object

    :param options: The options given to the directive: an object with attributes ``inherited_members``,
                    ``undoc_members``, ``show_inheritance`` and ``noindex`` that are ``True`` if the flag option of same
                    name was given to the auto directive
    :type options: object

    :param lines: A list of strings – the lines of the processed docstring – that the event handler can modify in place
                  to change what Sphinx puts into the output.
    :type lines: list [ str ]

    :return: The modified list of lines
    :rtype: list [ str ]
    """
    if inspect.isclass(obj) and issubclass(obj, django.db.models.Model):
        # Intersphinx mapping to django.contrib.postgres documentation does not work, so here the manual link
        postgres_docu = (
            intersphinx_mapping.get("django")[1][0] + "ref/contrib/postgres/fields/"
        )
        # include_hidden to get also ManyToManyFields
        for field in obj._meta.get_fields(include_hidden=True):
            field_type = type(field).__name__
            field_module = type(field).__module__
            if field_module == "django.contrib.postgres.fields.array":
                # Fix intersphinx mappings for django.contrib.postgres fields
                type_line = (
                    f":type {field.name}: `ArrayField <{postgres_docu}#arrayfield>`_"
                )
            elif field_module == "django.contrib.postgres.fields.jsonb":
                # Fix intersphinx mappings for django.contrib.postgres fields
                type_line = (
                    f":type {field.name}: `JSONField <{postgres_docu}#jsonfield>`_"
                )
            elif field_module in ["django.db.models.fields.related", "mptt.fields"]:
                # Fix intersphinx mappings for related fields (ForeignKey, OneToOneField, ManyToManyField, ...)
                # Also includes related MPTT fields (TreeForeignKey, TreeOneToOneField, TreeManyToManyField, ...)
                remote_model = field.remote_field.get_related_field().model
                type_line = f":type {field.name}: {field_type} to :class:`~{remote_model.__module__}.{remote_model.__name__}`"
            elif field_module == "django.db.models.fields.reverse_related":
                # Fix intersphinx mappings for reverse related fields (ManyToOneRel, OneToOneRel, ManyToManyRel, ...)
                remote_model = field.remote_field.model
                type_line = f":type {field.name}: Reverse {field_type[:-3]} Relation from :class:`~{remote_model.__module__}.{remote_model.__name__}`"
            else:
                if "django.db.models" in field_module:
                    # Scope with django.db.models * imports (remove all sub-module-paths)
                    field_module = "django.db.models"
                # Fix type hint to enable correct intersphinx mappings to other documentations
                type_line = f":type {field.name}: ~{field_module}.{field_type}"
            # This loop gets the indexes which are needed to update the type hints of the model parameters.
            # It makes it possible to split the parameter section into multiple parts, e.g. params inherited from a base
            # model and params of a sub model (otherwise the type hints would not be recognized when separated from
            # the parameter description).
            param_index = None
            next_param_index = None
            type_index = None
            for index, line in enumerate(lines):
                if param_index is None and f":param {field.name}:" in line:
                    # The index of the field param is only used to determine the next param line
                    param_index = index
                elif (
                    param_index is not None
                    and next_param_index is None
                    and (":param " in line or line == "")
                ):
                    # The line of the next param after the field, this is the index where we will insert the type.
                    # Sometimes the param descriptions extend over multiple lines, so we cannot just do param_index + 1.
                    # If the line is empty, the param description is finished, even if it extends over multiple lines.
                    next_param_index = index
                elif type_index is None and f":type {field.name}:" in line:
                    # The index of the old type hint, we will either move this line or replace it
                    type_index = index
                    break
            if next_param_index is None:
                # In case the current field is the last param, we just append the type at the very end of lines
                next_param_index = len(lines)
            # For some params, the type line is not automatically generated and thus the type_index might be `None`
            if type_index is not None:
                # We delete the old type index, because we will replace it with the new type line
                del lines[type_index]
            # Insert the new type line just before the next param
            lines.insert(next_param_index, type_line)
    return lines


# -- Source Code links to GitHub ---------------------------------------------


def linkcode_resolve(domain, info):
    """
    This function adds source code links to all modules (see :mod:`sphinx:sphinx.ext.linkcode`).
    It links all classes and functions to their source files on GitHub including line numbers.

    :param domain: The programming language of the given object (e.g. ``py``, ``c``, ``cpp`` or ``javascript``)
    :type domain: str

    :param info: Information about the given object. For a python object, it has the keys ``module`` and ``fullname``.
    :type info: dict

    :return: The URL of the given module on GitHub
    :rtype: str
    """
    if domain != "py" or not info["module"]:
        return None
    filename = info["module"].replace(".", "/")
    module = importlib.import_module(info["module"])
    basename = os.path.splitext(module.__file__)[0]
    if basename.endswith("__init__"):
        filename += "/__init__"
    item = module
    line_number_reference = ""
    for piece in info["fullname"].split("."):
        item = getattr(item, piece)
        try:
            line_number_reference = f"#L{inspect.getsourcelines(item)[1]}"
        except (TypeError, IOError):
            pass
    return f"https://github.com/Integreat/cms-django/blob/develop/src/{filename}.py{line_number_reference}"
