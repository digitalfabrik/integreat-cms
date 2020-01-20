'''
Expansion of API-Endpoints for the CMS
'''
from django.conf.urls import include, url

from .v3.feedback import feedback
from .v3.languages import languages
from .v3.pages import pages
from .v3.push_notifications import sent_push_notifications
from .v3.regions import regions, liveregions, hiddenregions, pushnew
from .v3.extras import extras
from .v3.accommodations import accommodations

urlpatterns = [
    url(r'regions/$', regions, name='regions'),
    url(r'regions/live/$', liveregions, name='liveregions'),
    url(r'regions/hidden/$', hiddenregions, name='hiddenregions'),
    url(r'regions/pushnew/$', pushnew, name='pushnew'),
    url(r'(?P<region_slug>[-\w]+)/', include([
        url(r'languages/$', languages),
        url(r'extras/$', extras),
        url(r'(?P<lan_code>[-\w]+)/sent_push_notifications/$', sent_push_notifications),
        url(r'(?P<languages>[-\w]+)/feedback/$', feedback),
        url(r'(?P<language_code>[-\w]+)/pages/$', pages),
        url(r'(?P<language_code>[-\w]+)/extras/$', extras),
        url(r'(?P<language_code>[-\w]+)/accommodations/$', accommodations)
    ])),
]
