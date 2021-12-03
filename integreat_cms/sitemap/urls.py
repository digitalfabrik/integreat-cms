"""
Django URL dispatcher for the sitemap package.
It contains the following routes:

* ``/sitemap.xml`` is routed to :mod:`~integreat_cms.sitemap.views.SitemapIndexView`

* ``/<region_slug>/<language_slug>/sitemap.xml`` is routed to :mod:`~integreat_cms.sitemap.views.SitemapView`

See :mod:`~integreat_cms.core.urls` for the other namespaces of this application.

For more information on this file, see :doc:`topics/http/urls`.
"""
from django.urls import path

from .views import SitemapIndexView, SitemapView


#: The namespace for this URL config (see :attr:`django.urls.ResolverMatch.app_name`)
app_name = "sitemap"

#: The url patterns of this module (see :doc:`topics/http/urls`)
urlpatterns = [
    path("sitemap.xml", SitemapIndexView.as_view(), name="index"),
    path(
        "<slug:region_slug>/<slug:language_slug>/sitemap.xml",
        SitemapView.as_view(),
        name="region_language",
    ),
]
