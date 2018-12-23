from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from .views import general, registration, pages


urlpatterns = [
    url(r'^$', general.DashboardView.as_view(), name='dashboard'),

    url(r'pages/$', pages.PageTreeView.as_view(), name='pages'),
    url(r'pages/new$', pages.PageView.as_view(), name='new_page'),
    url(r'pages/(?P<page_translation_id>[0-9]+)$',
        pages.PageView.as_view(),
        name='edit_page'),
    url(r'pages/(?P<page_translation_id>[0-9]+)/delete$',
        pages.PageView.as_view(),
        name='delete_page'),
    url(r'pages/archive$', pages.archive, name='archived_pages'),

    url(r'^login/$', registration.login, name='login'),
    url(r'^logout/$', registration.logout, name='logout'),
    url(r'^password_reset/$',
        auth_views.PasswordResetView.as_view(),
        name='password_reset'),
    url(r'^password_reset/done/$',
        registration.password_reset_done,
        name='password_reset_done'),
    url(r'^password_reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        auth_views.PasswordResetConfirmView.as_view
        (form_class=registration.forms.PasswordResetConfirmForm),
        name='password_reset_confirm'),
    url(r'^password_reset/complete/$',
        registration.password_reset_complete,
        name='password_reset_complete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
