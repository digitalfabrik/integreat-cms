"""
Django URL dispatcher.
Delegates the following namespaces:

* ``/api/`` to :mod:`~integreat_cms.api.urls`

* ``/admin/`` to :meth:`django.contrib.admin.ModelAdmin.get_urls`

* ``/i18n/`` to :mod:`django.conf.urls.i18n`

* ``/sitemap.xml`` and ``/<region_slug>/<language_slug>/sitemap.xml`` to :mod:`~integreat_cms.sitemap.urls`

* ``/`` to :mod:`~integreat_cms.cms.urls`

Additionally, the error handlers in :mod:`~integreat_cms.cms.views.error_handler` are referenced here (see :doc:`django:ref/urls`).

For more information on this file, see :doc:`django:topics/http/urls`.
"""
from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin


#: The url patterns of this module (see :doc:`django:topics/http/urls`)
urlpatterns = [
    path("", include("integreat_cms.api.urls")),
    path(
        "i18n/",
        include(
            (
                "django.conf.urls.i18n",
                "i18n",
            )
        ),
    ),
]

# Add url patterns of debug views
if settings.DEBUG:
    # Admin endpoint is only visible in debug mode
    urlpatterns.append(path("admin/", admin.site.urls))
    # The Django debug toolbar urlpatterns will only be activated if the debug_toolbar app is installed
    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))

# Unfortunately we need to do this in such way, as the admin endpoint needs to be added before the endpoints of the other apps.
urlpatterns += [
    path("", include("integreat_cms.sitemap.urls")),
    path("", include("integreat_cms.cms.urls")),
    path(
        "",
        include(
            (
                static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
                "media_files",
            )
        ),
    ),
    path(
        "",
        include(
            (
                static(settings.PDF_URL, document_root=settings.PDF_ROOT),
                "pdf_files",
            )
        ),
    ),
    path(
        "",
        include(
            (
                static(settings.XLIFF_URL, document_root=settings.XLIFF_DOWNLOAD_DIR),
                "xliff_files",
            )
        ),
    ),
]

handler400 = "integreat_cms.cms.views.error_handler.handler400"
handler403 = "integreat_cms.cms.views.error_handler.handler403"
handler404 = "integreat_cms.cms.views.error_handler.handler404"
handler500 = "integreat_cms.cms.views.error_handler.handler500"
