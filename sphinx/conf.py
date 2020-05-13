"""
Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Path setup --------------------------------------------------------------

import os
import sys
import inspect
import importlib
import django

from sphinx.writers.html import HTMLTranslator

from backend.settings import VERSION

# Append project source directory to path environment variable
sys.path.append(os.path.abspath('../src/'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'


# Setup Django
django.setup()


def setup(app):
    """
    Registeration and setup.

    This method does the initial setup for the docs generation.
    """
    # Register the docstring processor with sphinx to improve the appearance of Django models
    app.connect('autodoc-process-docstring', process_django_models)
    # Patch HTMLTranslator to open external links in new tab
    app.set_translator('html', PatchedHTMLTranslator)


# -- Project information -----------------------------------------------------


project = 'integreat-cms'
# pylint: disable=redefined-builtin
copyright = '2020, Integreat'
author = 'Integreat'

# The full version, including alpha/beta/rc tags
release = VERSION

# -- General configuration ---------------------------------------------------

# All enabled sphinx extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.githubpages',
    'sphinx.ext.intersphinx',
    'sphinx.ext.linkcode',
    'sphinxcontrib_django',
    'sphinx_rtd_theme',
]

# Enable cross-references to other documentations
intersphinx_mapping = {
    'python': ('https://docs.python.org/3.7', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
    'django': ('https://docs.djangoproject.com/en/2.2/',
               'https://docs.djangoproject.com/en/2.2/_objects/'),
    'django-mptt': ('https://django-mptt.readthedocs.io/en/latest/', None),
}

# The path for patched template files
templates_path = ['templates']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.
html_theme = 'sphinx_rtd_theme'
# Do not show the project name, only the logo
html_theme_options = {
    'logo_only': True,
    'collapse_navigation': False,
}
# The logo shown in the menu bar
html_logo = '../src/cms/static/images/integreat-logo-white.png'
# The facivon of the html doc files
html_favicon = '../src/cms/static/images/favicon.ico'
# The url where the docs should be published (via gh-pages)
html_baseurl = 'https://Integreat.github.io/cms-django/'
# Do not include links to the documentation source (.rst files) in build
html_show_sourcelink = False

# -- Modify default Django model parameter types------------------------------


# pylint: disable=unused-argument, too-many-locals, too-many-branches
def process_django_models(app, what, name, obj, options, lines):
    """Append correct param types from fields to model documentation."""
    if inspect.isclass(obj) and issubclass(obj, django.db.models.Model):
        # Intersphinx mapping to django.contrib.postgres documentation does not work, so here the manual link
        postgres_docu = intersphinx_mapping.get('django')[1][0] + 'ref/contrib/postgres/fields/'
        # include_hidden to get also ManyToManyFields
        for field in obj._meta.get_fields(include_hidden=True):
            field_type = type(field).__name__
            field_module = type(field).__module__
            if field_module == 'django.contrib.postgres.fields.array':
                # Fix intersphinx mappings for django.contrib.postgres fields
                type_line = ':type {}: `{}.ArrayField <{}#arrayfield>`_'.format(
                    field.name,
                    field_module,
                    postgres_docu
                )
            elif field_module == 'django.contrib.postgres.fields.jsonb':
                # Fix intersphinx mappings for django.contrib.postgres fields
                type_line = ':type {}: `{}.JSONField <{}#jsonfield>`_'.format(
                    field.name,
                    field_module,
                    postgres_docu
                )
            elif field_module in ['django.db.models.fields.related', 'mptt.fields']:
                # Fix intersphinx mappings for related fields (ForeignKey, OneToOneField, ManyToManyField, ...)
                # Also includes related MPTT fields (TreeForeignKey, TreeOneToOneField, TreeManyToManyField, ...)
                remote_model = field.remote_field.get_related_field().model
                type_line = ':type {}: {} to :class:`~{}.{}`'.format(
                    field.name,
                    field_type,
                    remote_model.__module__,
                    remote_model.__name__
                )
            elif field_module == 'django.db.models.fields.reverse_related':
                # Fix intersphinx mappings for reverse related fields (ManyToOneRel, OneToOneRel, ManyToManyRel, ...)
                remote_model = field.remote_field.model
                type_line = ':type {}: Reverse {} Relation from :class:`~{}.{}`'.format(
                    field.name,
                    field_type[:-3],
                    remote_model.__module__,
                    remote_model.__name__
                )
            else:
                if 'django.db.models' in field_module:
                    # Scope with django.db.models * imports (remove all sub-module-paths)
                    field_module = 'django.db.models'
                # Fix type hint to enable correct intersphinx mappings to other documentations
                type_line = ':type {}: {}.{}'.format(
                    field.name,
                    field_module,
                    field_type
                )
            # This loop gets the indexes which are needed to update the type hints of the model parameters.
            # It makes it possible to split the parameter section into multiple parts, e.g. params inherited from a base
            # model and params of a sub model (otherwise the type hints would not be recognized when separated from
            # the parameter description).
            param_index = None
            next_param_index = None
            type_index = None
            for index, line in enumerate(lines):
                if param_index is None and ':param {}:'.format(field.name) in line:
                    # The index of the field param is only used to determine the next param line
                    param_index = index
                elif param_index is not None and next_param_index is None and (':param ' in line or line == ''):
                    # The line of the next param after the field, this is the index where we will insert the type.
                    # Sometimes the param descriptions extend over multiple lines, so we cannot just do param_index + 1.
                    # If the line is empty, the param description is finished, even if it extends over multiple lines.
                    next_param_index = index
                elif type_index is None and ':type {}:'.format(field.name) in line:
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
    """Link source code to GitHub."""
    if domain != 'py' or not info['module']:
        return None
    filename = info['module'].replace('.', '/')
    module = importlib.import_module(info['module'])
    basename = os.path.splitext(module.__file__)[0]
    if basename.endswith('__init__'):
        filename += '/__init__'
    item = module
    line_number_reference = ''
    for piece in info['fullname'].split('.'):
        item = getattr(item, piece)
        try:
            line_number_reference = '#L{}'.format(
                inspect.getsourcelines(item)[1]
            )
        except (TypeError, IOError):
            pass
    return "https://github.com/Integreat/cms-django/blob/develop/src/{}.py{}".format(
        filename,
        line_number_reference
    )

# -- Link targets ------------------------------------------------------------


# pylint: disable=abstract-method
class PatchedHTMLTranslator(HTMLTranslator):
    """Open external links in a new tab"""

    def visit_reference(self, node):
        if (
                node.get('newtab') or
                not (
                    node.get('target') or
                    node.get('internal') or
                    'refuri' not in node
                )
        ):
            node['target'] = '_blank'
        super().visit_reference(node)
