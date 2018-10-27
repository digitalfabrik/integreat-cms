from django.conf.urls import url
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^reset-password/$', auth_views.PasswordResetView.as_view(), name='reset-password'),
    url(r'^change-password/$', auth_views.PasswordChangeView.as_view(), name='change-password'),
]