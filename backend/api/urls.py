from django.conf.urls import include, url

from .v3.languages import languages
from .v3.sites import sites, livesites, hiddenites, pushnew

urlpatterns = [
    url(r'sites/$', sites, name='sites'),
    url(r'sites/live/$', livesites, name='livesites'),
    url(r'sites/hidden/$', hiddenites, name='hiddensites'),
    url(r'sites/pushnew/$', pushnew, name='pushnew'),
    url(r'(?P<site_slug>[-\w]+)/', include([
        url(r'languages$', languages),
    ])),
]
