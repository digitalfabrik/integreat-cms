from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views

from . import views
from .legacy import sites

urlpatterns = [
    url(r'sites/$', sites, name='sites'),
]
