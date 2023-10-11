"""
Django URL dispatcher for the cms package.
See :mod:`~integreat_cms.core.urls` for the other namespaces of this application.

For more information on this file, see :doc:`django:topics/http/urls`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import include, path

if TYPE_CHECKING:
    from django.urls.resolvers import URLPattern


#: The url patterns of this module (see :doc:`django:topics/http/urls`)
urlpatterns: list[URLPattern] = [
    path("", include("integreat_cms.cms.urls.public")),
    path("", include("integreat_cms.cms.urls.protected")),
]
