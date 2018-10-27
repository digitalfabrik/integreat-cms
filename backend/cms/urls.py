from django.conf.urls import url
from django.contrib.auth import views as auth_views
from .views import general


urlpatterns = [
    url(r'^$', general.index),
    url(r'^login/$', general.login),
    url(r'^logout/$', general.logout),
    url(r'^reset-password/$', auth_views.PasswordResetView.as_view(), name='reset-password'),
    url(r'^change-password/$', auth_views.PasswordChangeView.as_view(), name='change-password'),
]