from django.conf.urls import include, url

from .v3 import views
from .v3.languages import languages
from .v3.sites import sites, livesites, hiddenites, pushnew
from .v3.push_notifications import sent_push_notifications

urlpatterns = [
    url('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'(?P<site>\d+)/extras/$', views.Extras.as_view()),
    url(r'sites/$', sites, name='sites'),
    url(r'sites/live/$', livesites, name='livesites'),
    url(r'sites/hidden/$', hiddenites, name='hiddensites'),
    url(r'sites/pushnew/$', pushnew, name='pushnew'),
    url(r'(?P<site_slug>[-\w]+)/', include([
        url(r'languages$', languages),
        url(r'(?P<lan_code>[-\w]+)/sent_push_notifications/$', sent_push_notifications),
    ])),
]
