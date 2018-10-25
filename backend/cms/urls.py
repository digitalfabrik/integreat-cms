from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', auth_views.LoginView.as_view(template_name='login.html')),
    #url(r'^logout/$', views.logout, name='logout'),
    #url(r'^reset-password/$', views.logout, name='reset-password'),
]