"""Provides routing to all submodules inside the application
"""
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from .views import general, registration, pages, regions, languages, language_tree, push_notifications
from .views.statistics import statistics


urlpatterns = [
    url(r'^$', general.AdminDashboardView.as_view(), name='admin_dashboard'),
    url(r'^regions/', include([
        url(r'^$', regions.RegionListView.as_view(), name='regions'),
        url(r'^new$', regions.RegionView.as_view(), name='new_region'),
        url(r'^(?P<region_slug>[-\w]+)/', include([
            url(
                r'^edit$',
                regions.RegionView.as_view(),
                name='edit_region'
            ),
            url(
                r'^delete$',
                regions.RegionView.as_view(),
                name='delete_region'
            ),
        ])),
    ])),
    url(r'^languages/', include([
        url(r'^$', languages.LanguageListView.as_view(), name='languages'),
        url(r'^new$', languages.LanguageView.as_view(), name='new_language'),
        url(r'^(?P<language_code>[-\w]+)/', include([
            url(
                r'^edit$',
                languages.LanguageView.as_view(),
                name='edit_language'
            ),
            url(
                r'^delete$',
                languages.LanguageView.as_view(),
                name='delete_language'
            ),
        ])),
    ])),

    url(r'^settings/$', general.AdminSettingsView.as_view(), name='admin_settings'),
    url(r'^login/$', registration.login, name='login'),
    url(r'^logout/$', registration.logout, name='logout'),
    url(r'^password_reset/', include([
        url(
            r'$',
            auth_views.PasswordResetView.as_view(),
            name='password_reset'
        ),
        url(
            r'^done/$',
            registration.password_reset_done,
            name='password_reset_done'
        ),
        url(
            r'^(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
            auth_views.PasswordResetConfirmView.as_view
            (form_class=registration.forms.PasswordResetConfirmForm),
            name='password_reset_confirm'
        ),
        url(
            r'^complete/$',
            registration.password_reset_complete,
            name='password_reset_complete'
        ),
    ])),

    url(r'^(?P<site_slug>[-\w]+)/', include([
        url(r'^$', general.DashboardView.as_view(), name='dashboard'),
        url(r'^pages/', include([
            url(r'^$', pages.PageTreeView.as_view(), name='pages'),
            url(r'^(?P<language_code>[-\w]+)/', include([
                url(r'^$', pages.PageTreeView.as_view(), name='pages'),
                url(r'^new$', pages.PageView.as_view(), name='new_page'),
                url(r'^(?P<page_id>[0-9]+)/', include([
                    url(
                        r'^edit$',
                        pages.PageView.as_view(),
                        name='edit_page'
                    ),
                    url(
                        r'^sbs_edit$',
                        pages.SBSPageView.as_view(),
                        name='sbs_edit_page'
                    ),
                    url(
                        r'^archive$',
                        pages.archive_page,
                        name='archive_page'
                    ),
                    url(
                        r'^restore$',
                        pages.restore_page,
                        name='restore_page'
                    ),
                    url(
                        r'^delete$',
                        pages.PageView.as_view(),
                        name='delete_page'
                    ),
                ])),
                url(r'^archive$', pages.ArchivedPagesView.as_view(), name='archived_pages'),
            ])),
        ])),
        url(r'^push_notifications/', include([
            url(r'^$', push_notifications.PushNotificationListView.as_view(), name='push_notifications'),
            url(r'^(?P<language_code>[-\w]+)/', include([
                url(r'^$', push_notifications.PushNotificationListView.as_view(), name='push_notifications'),
                url(r'^new$', push_notifications.PushNotificationView.as_view(), name='new_push_notification'),
                url(r'^(?P<push_notification_id>[0-9]+)/', include([
                    url(
                        r'^edit$',
                        push_notifications.PushNotificationView.as_view(),
                        name='edit_push_notification'
                    ),
                ])),
            ])),
        ])),
        url(r'^language-tree/', include([
            url(r'^$', language_tree.LanguageTreeView.as_view(), name='language_tree'),
            url(
                r'^new$',
                language_tree.LanguageTreeNodeView.as_view(),
                name='new_language_tree_node'
            ),
            url(r'^(?P<language_tree_node_id>[0-9]+)/', include([
                url(
                    r'^edit$',
                    language_tree.LanguageTreeNodeView.as_view(),
                    name='edit_language_tree_node'
                ),
                url(
                    r'^delete$',
                    language_tree.LanguageTreeNodeView.as_view(),
                    name='delete_language_tree_node'
                ),
            ])),
        ])),
        url(r'^statistics/$', statistics.AnalyticsView.as_view(), name='statistics'),
        url(r'^settings/$', general.SettingsView.as_view(), name='settings'),
    ])),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
