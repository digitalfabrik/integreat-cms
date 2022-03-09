from django.conf import settings
from django.urls import include, path
from django.views.static import serve

from integreat_cms.core.urls import urlpatterns

#: Add the debug serve view to test the download of XLIFF files
urlpatterns += [
    path(
        "",
        include(
            (
                [
                    path(
                        f"{settings.XLIFF_URL}<path:path>".lstrip("/"),
                        serve,
                        {"document_root": settings.XLIFF_DOWNLOAD_DIR},
                    )
                ],
                "xliff_files",
            )
        ),
    ),
]
