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


# pylint: disable=unused-argument
def process_django_models(app, what, name, obj, options, lines):
    """Append correct param types from fields to model documentation."""
    if inspect.isclass(obj) and issubclass(obj, django.db.models.Model):
        # Intersphinx mapping to django.contrib.postgres documentation does not work, so here the manual link
        postgres_docu = 'https://docs.djangoproject.com/en/2.2/ref/contrib/postgres/fields/'
        for field in obj._meta.fields:
            field_type = type(field)
            module = field_type.__module__
            # Fix intersphinx mappings for django.contrib.postgres fields
            if module == 'django.contrib.postgres.fields.array':
                lines.append(
                    ':type {}: `{}.ArrayField <{}#arrayfield>`_'.format(
                        field.attname,
                        module,
                        postgres_docu
                    )
                )
                continue
            if module == 'django.contrib.postgres.fields.jsonb':
                lines.append(
                    ':type {}: `{}.JSONField <{}#jsonfield>`_'.format(
                        field.attname,
                        module,
                        postgres_docu
                    )
                )
                continue
            if 'django.db.models' in module:
                # scope with django.db.models * imports
                module = 'django.db.models'
            lines.append(
                ':type {}: {}.{}'.format(
                    field.attname,
                    module,
                    field_type.__name__
                )
            )
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
