"""
Django URL dispatcher for the sitemap package.
It contains the following routes:

* ``/sitemap.xml`` is routed to :mod:`~integreat_cms.sitemap.views.SitemapIndexView`

* ``/<region_slug>/<language_slug>/sitemap.xml`` is routed to :mod:`~integreat_cms.sitemap.views.SitemapView`

See :mod:`~integreat_cms.core.urls` for the other namespaces of this application.

For more information on this file, see :doc:`django:topics/http/urls`.
"""
from django.urls import path, include

from .views import SitemapIndexView, SitemapView


#: The namespace for this URL config (see :attr:`django.urls.ResolverMatch.app_name`)
app_name = "sitemap"

#: The url patterns of this module (see :doc:`django:topics/http/urls`)
urlpatterns = [
    path("sitemap.xml", SitemapIndexView.as_view(), name="index"),
    path("wp-json/ig-sitemap/v1/sitemap-index.xml", SitemapIndexView.as_view()),
    path(
        "<slug:region_slug>/<slug:language_slug>/",
        include(
            [
                path(
                    "sitemap.xml",
                    SitemapView.as_view(),
                    name="region_language",
                ),
                path(
                    "wp-json/ig-sitemap/v1/sitemap.xml",
                    SitemapView.as_view(),
                ),
            ]
        ),
    ),
]
