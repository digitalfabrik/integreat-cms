"""Provides routing to all submodules inside the application
"""
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings as django_settings
from django.contrib.auth import views as auth_views

from .views import analytics
from .views import dashboard
from .views import languages
from .views import language_tree
from .views import media
from .views import pages
from .views import pois
from .views import push_notifications
from .views import organizations
from .views import settings
from .views import statistics
from .views import regions
from .views import registration
from .views import roles
from .views import users


urlpatterns = [
    url(r'^$', dashboard.RedirectView.as_view(), name='redirect'),
    url(r'^admin_dashboard/$', dashboard.AdminDashboardView.as_view(), name='admin_dashboard'),
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
    url(r'^users/', include([
        url(r'^$', users.UserListView.as_view(), name='users'),
        url(r'^new$', users.UserView.as_view(), name='new_user'),
        url(r'^(?P<user_id>[0-9]+)/', include([
            url(
                r'^edit$',
                users.UserView.as_view(),
                name='edit_user'
            ),
            url(
                r'^delete$',
                users.delete_user,
                name='delete_user'
            ),
        ])),
    ])),
    url(r'^roles/', include([
        url(r'^$', roles.RoleListView.as_view(), name='roles'),
        url(r'^new$', roles.RoleView.as_view(), name='new_role'),
        url(r'^(?P<role_id>[0-9]+)/', include([
            url(
                r'^edit$',
                roles.RoleView.as_view(),
                name='edit_role'
            ),
            url(
                r'^delete$',
                roles.RoleView.as_view(),
                name='delete_role'
            ),
        ])),
    ])),
    url(r'^organizations/', include([
        url(r'^$', organizations.OrganizationListView.as_view(), name='organizations'),
        url(r'^new$', organizations.OrganizationView.as_view(), name='new_organization'),
        url(r'^(?P<organization_id>[0-9]+)/', include([
            url(
                r'^edit$',
                organizations.OrganizationView.as_view(),
                name='edit_organization'
            ),
            url(
                r'^delete$',
                organizations.OrganizationView.as_view(),
                name='delete_organization'
            ),
        ])),
    ])),

    url(r'^settings/$', settings.AdminSettingsView.as_view(), name='admin_settings'),
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

    url(r'^ajax/', include([
        url(
            r'^grant_page_permission$',
            pages.grant_page_permission_ajax,
            name='grant_page_permission_ajax'
        ),
        url(
            r'^revoke_page_permission$',
            pages.revoke_page_permission_ajax,
            name='revoke_page_permission_ajax'
        ),
    ])),

    url(r'^(?P<region_slug>[-\w]+)/', include([
        url(r'^$', dashboard.DashboardView.as_view(), name='dashboard'),
        url(r'^translation_coverage/', analytics.TranslationCoverageView.as_view(), name='translation_coverage'),
        url(r'^pages/', include([
            url(r'^$', pages.PageTreeView.as_view(), name='pages'),
            url(r'^(?P<language_code>[-\w]+)/', include([
                url(r'^$', pages.PageTreeView.as_view(), name='pages'),
                url(r'^new$', pages.PageView.as_view(), name='new_page'),
                url(r'^upload$', pages.upload_page, name='upload_page'),
                url(r'^(?P<page_id>[0-9]+)/', include([
                    url(
                        r'^view$',
                        pages.view_page,
                        name='view_page'
                    ),
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
                    url(
                        r'^download$',
                        pages.download_page_xliff,
                        name='download_page'
                    ),
                ])),
                url(r'^archive$', pages.ArchivedPagesView.as_view(), name='archived_pages'),
            ])),
        ])),
        url(r'^pois/', include([
            url(r'^$', pois.POIListView.as_view(), name='pois'),
            url(r'^(?P<language_code>[-\w]+)/', include([
                url(r'^$', pois.POIListView.as_view(), name='pois'),
                url(r'^new$', pois.POIView.as_view(), name='new_poi'),
                url(r'^(?P<poi_id>[0-9]+)/', include([
                    url(
                        r'^view$',
                        pois.view_poi,
                        name='view_poi'
                    ),
                    url(
                        r'^edit$',
                        pois.POIView.as_view(),
                        name='edit_poi'
                    ),
                    url(
                        r'^archive$',
                        pois.archive_poi,
                        name='archive_poi'
                    ),
                    url(
                        r'^restore$',
                        pois.restore_poi,
                        name='restore_poi'
                    ),
                    url(
                        r'^delete$',
                        pois.POIView.as_view(),
                        name='delete_poi'
                    ),
                ])),
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
        url(r'^settings/$', settings.SettingsView.as_view(), name='settings'),
        url(r'^media/', include([
            url(r'^$', media.MediaListView.as_view(), name='media'),
            url(r'^(?P<document_id>[0-9]+)/', include([
                url(r'^new$', media.MediaEditView.as_view(), name='new_upload_file'),
                url(r'^edit$', media.MediaEditView.as_view(), name='edit_file'),
                url(r'^delete$', media.delete_file, name='delete_file'),
            ])),
        ])),
        url(r'^users/', include([
            url(r'^$', users.RegionUserListView.as_view(), name='region_users'),
            url(r'^new$', users.RegionUserView.as_view(), name='new_region_user'),
            url(r'^(?P<user_id>[0-9]+)/', include([
                url(
                    r'^edit$',
                    users.RegionUserView.as_view(),
                    name='edit_region_user'
                ),
                url(
                    r'^delete$',
                    users.delete_region_user,
                    name='delete_region_user'
                ),
            ])),
        ])),
    ])),
] + static(django_settings.MEDIA_URL, document_root=django_settings.MEDIA_ROOT)
