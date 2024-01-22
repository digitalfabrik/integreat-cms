"""
Configuration file for the Sphinx documentation builder.

This file only contains the options which deviate from the default values.
For a full list see the documentation: :doc:`sphinx:usage/configuration`
"""


# -- Path setup --------------------------------------------------------------

from __future__ import annotations

import contextlib
import importlib
import inspect
import os
import sys
from datetime import date
from typing import Final

from django import VERSION as django_version_tuple
from sphinx.application import Sphinx

from integreat_cms.core import settings

# Append project source directory to path environment variable
sys.path.append(os.path.abspath("../.."))
# Append sphinx source directory to path environment variable to allow documentation for this file
sys.path.append(os.path.abspath("."))
#: The path to the django settings module (see :doc:`sphinxcontrib-django:readme`)
django_settings: Final[str] = "integreat_cms.core.sphinx_settings"
#: The "major.minor" version of Django
django_version: Final[str] = f"{django_version_tuple[0]}.{django_version_tuple[1]}"

# -- Project information -----------------------------------------------------

#: The project name
project: Final[str] = "integreat-cms"
# pylint: disable=redefined-builtin
#: The copyright notice
copyright: Final[str] = f"{date.today().year} {settings.COMPANY}"
#: The project author
author: Final[str] = settings.COMPANY
#: GitHub username
github_username: Final[str] = "digitalfabrik"
#: GitHub repository name
github_repository: Final[str] = "integreat-cms"
#: GitHub URL
github_url: Final[str] = f"https://github.com/{github_username}/{github_repository}"
#: GitHub pages URL (target of gh-pages branch)
github_pages_url: Final[
    str
] = f"https://{github_username}.github.io/{github_repository}"
# GitHub URL of Django repository
django_github_url: Final[
    str
] = f"https://github.com/django/django/blob/stable/{django_version}.x"

#: The full version, including alpha/beta/rc tags
release = "2024.1.0"

# -- General configuration ---------------------------------------------------

#: All enabled sphinx extensions (see :ref:`sphinx-extensions`)
extensions: Final[list[str]] = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "sphinxcontrib_django",
    "sphinx_rtd_theme",
    "sphinx_last_updated_by_git",
]
#: Enable cross-references to other documentations
intersphinx_mapping: Final[dict[str, tuple[str, str | None]]] = {
    "aiohttp": ("https://docs.aiohttp.org/en/stable/", None),
    "dateutil": ("https://dateutil.readthedocs.io/en/stable/", None),
    "geopy": ("https://geopy.readthedocs.io/en/stable/", None),
    "lxml": ("https://lxml.de/apidoc/", None),
    "python": (
        f"https://docs.python.org/{sys.version_info.major}.{sys.version_info.minor}/",
        None,
    ),
    "pytest": ("https://docs.pytest.org/en/latest/", None),
    "pytest-cov": ("https://pytest-cov.readthedocs.io/en/latest/", None),
    "pytest-django": ("https://pytest-django.readthedocs.io/en/latest/", None),
    "pytest-httpserver": ("https://pytest-httpserver.readthedocs.io/en/latest/", None),
    "pytest-xdist": ("https://pytest-xdist.readthedocs.io/en/latest/", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
    "requests-mock": ("https://requests-mock.readthedocs.io/en/latest/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
    "sphinx-rtd-theme": (
        "https://sphinx-rtd-theme.readthedocs.io/en/latest/",
        None,
    ),
    "sphinxcontrib-django": (
        "https://sphinxcontrib-django.readthedocs.io/en/latest/",
        None,
    ),
    "sphinx-rtd-tutorial": (
        "https://sphinx-rtd-tutorial.readthedocs.io/en/latest/",
        None,
    ),
    "db_mutex": ("https://django-db-mutex.readthedocs.io/en/latest/", None),
    "django": (
        f"https://docs.djangoproject.com/en/{django_version}/",
        f"https://docs.djangoproject.com/en/{django_version}/_objects/",
    ),
    "django-debug-toolbar": (
        "https://django-debug-toolbar.readthedocs.io/en/latest/",
        None,
    ),
    "django-polymorphic": (
        "https://django-polymorphic.readthedocs.io/en/latest/",
        None,
    ),
    "django-treebeard": ("https://django-treebeard.readthedocs.io/en/latest/", None),
    "setuptools": ("https://setuptools.pypa.io/en/latest/", None),
    "twine": ("https://twine.readthedocs.io/en/latest/", None),
    "wsgi": ("https://wsgi.readthedocs.io/en/latest/", None),
    "xhtml2pdf": ("https://xhtml2pdf.readthedocs.io/en/latest/", None),
}
#: The intersphinx request timeout in seconds
intersphinx_timeout: Final[int] = 5
#: This value controls whether the types of undocumented parameters and return values are documented
autodoc_typehints: Final[str] = "both"
#: The path for patched template files
templates_path: Final[list[str]] = ["templates"]
#: Markup to shorten external links (see :doc:`sphinx:usage/extensions/extlinks`)
extlinks: Final[dict[str, tuple[str, str]]] = {
    "github": (f"{github_url}/%s", "%s"),
    "github-issue": (f"{github_url}/issues/%s", "#%s"),
    "github-source": (f"{github_url}/blob/develop/%s", "%s"),
    "django-source": (f"{django_github_url}/%s", "%s"),
}
#: A string of reStructuredText that will be included at the end of every source file that is read. Used for substitutions.
rst_epilog: Final[
    str
] = f"""
.. |github-username| replace:: {github_username}
.. |github-repository| replace:: {github_repository}
.. |github-pages-url| replace:: {github_pages_url}
"""
#: Warn about all references where the target cannot be found
nitpicky: Final[bool] = False
#: A list of (type, target) tuples that should be ignored when :attr:`nitpicky` is ``True``
nitpick_ignore: list[tuple[str, str]] = [
    ("py:attr", "django.contrib.auth.models.Group.role"),
    ("py:attr", "django.contrib.auth.models.Group.user_set"),
    ("py:attr", "django.contrib.auth.models.Permission.user_set"),
    (
        "py:attr",
        "django.contrib.contenttypes.models.ContentType.polymorphic_cms.feedback_set+",
    ),
    ("py:attr", "linkcheck.models.Link.+"),
    ("py:attr", "linkcheck.models.Link.event_translation"),
    ("py:attr", "linkcheck.models.Link.event_translations"),
    ("py:attr", "linkcheck.models.Link.imprint_translation"),
    ("py:attr", "linkcheck.models.Link.page_translation"),
    ("py:attr", "linkcheck.models.Link.page_translations"),
    ("py:attr", "linkcheck.models.Link.poi_translation"),
    ("py:attr", "linkcheck.models.Link.poi_translations"),
    ("py:class", "_io.StringIO"),
    ("py:class", "argparse.ArgumentTypeError"),
    ("py:class", "builtins.AssertionError"),
    ("py:class", "builtins.int"),
    ("py:class", "builtins.int"),
    ("py:class", "django.contrib.admin.checks.ModelAdminChecks"),
    ("py:class", "django.contrib.admin.helpers.ActionForm"),
    ("py:class", "django.contrib.auth.base_user.BaseUserManager"),
    ("py:class", "django.contrib.auth.context_processors.PermWrapper"),
    ("py:class", "django.contrib.auth.forms.UsernameField"),
    ("py:class", "django.contrib.auth.hashers.BCryptSHA256PasswordHasher"),
    ("py:class", "django.contrib.auth.tokens.PasswordResetTokenGenerator"),
    ("py:class", "django.core.handlers.WSGIHandler"),
    ("py:class", "django.core.mail.EmailMultiAlternatives"),
    ("py:class", "django.core.management.base.BaseCommand"),
    ("py:class", "django.core.management.base.CommandError"),
    ("py:class", "django.core.management.base.CommandParser"),
    ("py:class", "django.core.serializers.base.DeserializationError"),
    ("py:class", "django.core.serializers.base.DeserializedObject"),
    ("py:class", "django.core.serializers.base.ProgressBar"),
    ("py:class", "django.core.serializers.base.SerializationError"),
    ("py:class", "django.core.serializers.xml_serializer.Deserializer"),
    ("py:class", "django.core.serializers.xml_serializer.Serializer"),
    ("py:class", "django.db.models.base.ModelBase"),
    ("py:class", "django.forms.BaseInlineFormSet"),
    ("py:class", "django.forms.BaseModelFormSet"),
    ("py:class", "django.forms.formsets.POICategoryTranslationFormFormSet"),
    ("py:class", "django.forms.models.ModelChoiceIterator"),
    ("py:class", "django.forms.models.ModelFormMetaclass"),
    ("py:class", "django.forms.widgets.LanguageTreeNodeForm"),
    ("py:class", "django.forms.widgets.PageForm"),
    ("py:class", "django.test.client.AsyncClient"),
    ("py:class", "django.test.client.Client"),
    ("py:class", "django.utils.datastructures.MultiValueDict"),
    ("py:class", "django.utils.functional.Promise"),
    ("py:class", "django.utils.xmlutils.SimplerXMLGenerator"),
    ("py:class", "linkcheck.apps.LinkcheckConfig"),
    ("py:class", "linkcheck.Linklist"),
    ("py:class", "linkcheck.models.Link"),
    ("py:class", "linkcheck.models.Url"),
    ("py:class", "NoneType"),
    ("py:class", "polymorphic.query.PolymorphicQuerySet"),
    ("py:class", "PolymorphicQuerySet"),
    ("py:class", "pytest_django.fixtures.SettingsWrapper"),
    ("py:class", "requests_mock.mocker.Mocker"),
    ("py:class", "webauthn.WebAuthnUser"),
    ("py:class", "xml.dom.minidom.Element"),
    ("py:func", "django.contrib.sitemaps.Sitemap._urls"),
    ("py:func", "django.utils.text.capfirst"),
]
#: A list of prefixes that are ignored for sorting the Python module index
modindex_common_prefix: Final[list[str]] = ["integreat_cms"]

# -- Options for HTML output -------------------------------------------------

#: The theme to use for HTML and HTML Help pages.
html_theme: Final[str] = "sphinx_rtd_theme"
#: Do not show the project name, only the logo
html_theme_options: Final[dict[str, bool]] = {
    "logo_only": False,
    "collapse_navigation": False,
}
#: The logo shown in the menu bar
html_logo: Final[
    str
] = "../../integreat_cms/static/src/logos/integreat/integreat-logo-white.svg"
#: The favicon of the html doc files
html_favicon: Final[
    str
] = "../../integreat_cms/static/src/logos/integreat/integreat-icon.svg"
#: The url where the docs should be published (via gh-pages)
html_baseurl: Final[str] = github_pages_url
#: Do not include links to the documentation source (.rst files) in build
html_show_sourcelink: Final[bool] = False
#: Do not include a link to sphinx
html_show_sphinx: Final[bool] = False
#: Include last updated timestamp
html_last_updated_fmt: Final[str] = "%b %d, %Y"

# -- Source Code links to GitHub ---------------------------------------------


def linkcode_resolve(domain: str, info: dict) -> str | None:
    """
    This function adds source code links to all modules (see :mod:`sphinx:sphinx.ext.linkcode`).
    It links all classes and functions to their source files on GitHub including line numbers.

    :param domain: The programming language of the given object (e.g. ``py``, ``c``, ``cpp`` or ``javascript``)
    :param info: Information about the given object. For a python object, it has the keys ``module`` and ``fullname``.
    :return: The URL of the given module on GitHub
    """
    module_str = info["module"]
    if domain != "py" or not module_str:
        return None
    item = importlib.import_module(module_str)
    line_number_reference = ""
    for piece in info["fullname"].split("."):
        with contextlib.suppress(AttributeError, TypeError, IOError):
            item = getattr(item, piece)
            line_number_reference = f"#L{inspect.getsourcelines(item)[1]}"
            module_str = item.__module__
    module = importlib.import_module(module_str)
    module_path = module_str.replace(".", "/")
    filename = module.__file__.partition(module_path)[2] if module.__file__ else ""
    url = (
        django_github_url
        if module_str.startswith("django.")
        else f"{github_url}/blob/develop"
    )
    return f"{url}/{module_path}{filename}{line_number_reference}"


# -- Custom patches for autodoc ----------------------------------------------


def setup(app: Sphinx) -> None:
    """
    Connect to the ``django-configured`` event of :mod:`sphinxcontrib_django` to monkeypatch application.

    :param app: The Sphinx application object
    """
    # Add crossref type for links to the pytest documentation
    app.add_crossref_type(
        directivename="fixture",
        rolename="fixture",
        indextemplate="pair: %s; fixture",
    )
