from django.conf.urls import include, url

from .v3.languages import languages
from .v3.sites import sites, pushnew

urlpatterns = [
    url(r'sites/$', sites, name='sites'),
    url(r'sites/pushnew/$', pushnew, name='pushnew'),
    url(r'(?P<site_slug>[-\w]+)/', include([
        url(r'languages$', languages),
    ])),
]
