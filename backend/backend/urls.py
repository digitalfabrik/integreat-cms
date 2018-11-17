from django.conf.urls import (
    include,
    url,
    handler400,
    handler403,
    handler404,
    handler500
)
from django.contrib import admin


urlpatterns = [
    url(r'^', include('cms.urls')),
    url(r'^api/', include('api.urls')),
    url(r'^admin/', admin.site.urls),
]

handler400 = 'cms.views.general.handler400'
handler403 = 'cms.views.general.handler403'
handler404 = 'cms.views.general.handler404'
handler500 = 'cms.views.general.handler500'
