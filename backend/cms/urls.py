from django.conf.urls import url
from django.contrib.auth import views as auth_views
from .views import general, registration, pages


urlpatterns = [
    url(r'^$', general.DashboardView.as_view(), name='dashboard'),

    url(r'pages/$', pages.PagesView.as_view(), name='pages'),
    url(r'pages/new$', pages.NewPageView.as_view(), name='new_page'),
    url(r'pages/archive$', pages.archive, name='archived_pages'),

    url(r'^login/$', registration.login, name='login'),
    url(r'^logout/$', registration.logout, name='logout'),
    url(r'^password_reset/$', auth_views.PasswordResetView.as_view(form_class=registration.forms.PasswordResetForm), name='password_reset'),
    url(r'^password_reset/done/$', registration.password_reset_done, name='password_reset_done'),
    url(r'^password_reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.PasswordResetConfirmView.as_view(form_class=registration.forms.PasswordResetConfirmForm), name='password_reset_confirm'),
    url(r'^password_reset/complete/$', registration.password_reset_complete, name='password_reset_complete'),
]