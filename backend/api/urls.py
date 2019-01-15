from django.conf.urls import url

from .v3.languages import languages
from .v3.sites import sites, pushnew

urlpatterns = [
    url(r'sites/$', sites, name='sites'),
    url(r'(?P<site_name>\w+)/languages$', languages),
    url(r'sites/pushnew/$', pushnew, name='pushnew')
]
