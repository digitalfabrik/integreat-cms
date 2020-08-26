"""
Django URL dispatcher.
Delegates the following namespaces:

* ``/api/`` to :mod:`api.urls`

* ``/admin/`` to :meth:`django.contrib.admin.ModelAdmin.get_urls`

* ``/i18n/`` to :mod:`django.conf.urls.i18n`

* ``/sitemap.xml`` and ``/<region_slug>/<language_code>/sitemap.xml`` to :mod:`sitemap.urls`

* ``/`` to :mod:`cms.urls`

Additionally, the error handlers in :mod:`cms.views.error_handler` are referenced here (see :doc:`ref/urls`).

For more information on this file, see :doc:`topics/http/urls`.
"""
from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r"^api/", include("api.urls")),
    url(r"^admin/", admin.site.urls),
    url(r"^i18n/", include("django.conf.urls.i18n")),
    url(r"^", include("sitemap.urls")),
    url(r"^", include("cms.urls")),
]

handler400 = "cms.views.error_handler.handler400"
handler403 = "cms.views.error_handler.handler403"
handler404 = "cms.views.error_handler.handler404"
handler500 = "cms.views.error_handler.handler500"
