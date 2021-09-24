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

urlpatterns = [
    path("sitemap.xml", SitemapIndexView.as_view(), name="sitemap_index"),
    path(
        "<slug:region_slug>/<slug:language_slug>/sitemap.xml",
        SitemapView.as_view(),
        name="sitemap",
    ),
]
