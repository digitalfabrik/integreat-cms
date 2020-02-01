'''
Expansion of API-Endpoints for the CMS
'''
from django.conf.urls import include, url

from .v3.languages import languages
from .v3.regions import regions
from .v3.accommodations import accommodations

urlpatterns = [
    url(r'regions/$', regions, name='regions'),
    url(r'(?P<region_slug>[-\w]+)/', include([
        url(r'languages/$', languages),
        url(r'(?P<language_code>[-\w]+)/accommodations/$', accommodations)
    ])),
]
