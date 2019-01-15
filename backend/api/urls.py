from django.conf.urls import url

from .legacy.sites import sites, pushnew

urlpatterns = [
    url(r'sites/$', sites, name='sites'),
    url(r'sites/pushnew/$', pushnew, name='pushnew')
]
