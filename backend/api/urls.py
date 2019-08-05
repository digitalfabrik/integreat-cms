from django.conf.urls import include, url
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .v3 import views
from .v3.feedback import feedback
from .v3.languages import languages
from .v3.regions import regions, liveregions, hiddenregions, pushnew
from .v3.push_notifications import sent_push_notifications


schema_view = get_schema_view(
    openapi.Info(
        title="Integreat API",
        default_version='v1',
        description="Integreat API documentation",
        terms_of_service="https://integreat.app/disclaimer",
        contact=openapi.Contact(email="info@integreat-app.de"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    url('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'region/(?P<region>\d+)/extras/$', views.ExtrasView.as_view()),
    url(r'region/(?P<region>\d+)/locations/$', views.LocationView.as_view()),
    url(r'extra/(?P<id>\d+)/$', views.ExtraView.as_view()),
    url(r'regions/$', regions, name='regions'),
    url(r'regions/live/$', liveregions, name='liveregions'),
    url(r'regions/hidden/$', hiddenregions, name='hiddenregions'),
    url(r'regions/pushnew/$', pushnew, name='pushnew'),
    url(r'(?P<region_slug>[-\w]+)/', include([
        url(r'languages$', languages),
        url(r'(?P<lan_code>[-\w]+)/sent_push_notifications/$', sent_push_notifications),
        url(r'(?P<languages>[-\w]+)/feedback/$', feedback),
    ])),
]
