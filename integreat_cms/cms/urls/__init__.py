"""
Django URL dispatcher for the cms package.
See :mod:`~integreat_cms.core.urls` for the other namespaces of this application.

For more information on this file, see :doc:`django:topics/http/urls`.
"""

from django.conf.urls import include, url


#: The url patterns of this module (see :doc:`django:topics/http/urls`)
urlpatterns = [
    url(r"^", include("integreat_cms.cms.urls.public")),
    url(r"^", include("integreat_cms.cms.urls.protected")),
]
