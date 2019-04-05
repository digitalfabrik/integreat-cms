"""Provides routing to all submodules inside the application
"""
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from .views import general, registration, pages, regions
from .views.statistics import statistics


urlpatterns = [
    url(r'^$', general.AdminDashboardView.as_view(), name='admin_dashboard'),
    url(r'^regions/', include([
        url(r'^$', regions.RegionListView.as_view(), name='regions'),
        url(r'^new$', regions.RegionView.as_view(), name='new_region'),
        url(r'^(?P<region_slug>[-\w]+)', include([
            url(r'^$',
                regions.RegionView.as_view(),
                name='edit_region'
                ),
            url(r'^delete$',
                regions.RegionView.as_view(),
                name='delete_region'
                ),
        ])),
    ])),

    url(r'^login/$', registration.login, name='login'),
    url(r'^logout/$', registration.logout, name='logout'),
    url(r'^password_reset/', include([
        url(r'$',
            auth_views.PasswordResetView.as_view(),
            name='password_reset'
            ),
        url(r'^done/$',
            registration.password_reset_done,
            name='password_reset_done'
            ),
        url(r'^(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
            auth_views.PasswordResetConfirmView.as_view
            (form_class=registration.forms.PasswordResetConfirmForm),
            name='password_reset_confirm'
            ),
        url(r'^complete/$',
            registration.password_reset_complete,
            name='password_reset_complete'
            ),
    ])),

    url(r'^(?P<site_slug>[-\w]+)/', include([
        url(r'^$', general.DashboardView.as_view(), name='dashboard'),
        url(r'^pages/', include([
            url(r'^$', pages.PageTreeView.as_view(), name='pages'),
            url(r'^new$', pages.PageView.as_view(), name='new_page'),
            url(r'^(?P<page_translation_id>[0-9]+)', include([
                url(r'^$',
                    pages.PageView.as_view(),
                    name='edit_page'
                    ),
                url(r'^delete$',
                    pages.PageView.as_view(),
                    name='delete_page'
                    ),
            ])),
            url(r'^archive$', pages.archive, name='archived_pages'),
        ])),
        url(r'^statistics/$', statistics.AnalyticsView.as_view(), name='statistics'),
    ])),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
