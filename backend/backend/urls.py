from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r'^api/', include('api.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^', include('cms.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
]

handler400 = 'cms.views.error_handler.handler400'
handler403 = 'cms.views.error_handler.handler403'
handler404 = 'cms.views.error_handler.handler404'
handler500 = 'cms.views.error_handler.handler500'
