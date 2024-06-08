"""
This modules contains the config for the view tests
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from urllib import parse

from django.conf import settings
from django.urls import reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.models.pois.poi import get_default_opening_hours

from ...conftest import (
    ALL_ROLES,
    AUTHOR,
    CMS_TEAM,
    EDITOR,
    HIGH_PRIV_STAFF_ROLES,
    MANAGEMENT,
    OBSERVER,
    PRIV_STAFF_ROLES,
    ROLES,
    ROOT,
    SERVICE_TEAM,
    STAFF_ROLES,
    WRITE_ROLES,
)

if TYPE_CHECKING:
    import sys
    from typing import Any, Final, TypeAlias, Union

    ViewNameStr: TypeAlias = str
    ViewNameGetparams: TypeAlias = str
    ViewName: TypeAlias = Union[ViewNameStr, tuple[ViewNameStr, ViewNameGetparams]]
    Roles: TypeAlias = list[str]
    PostDataDict: TypeAlias = dict[str, Any]
    PostDataJSON: TypeAlias = str
    PostData: TypeAlias = Union[PostDataDict, PostDataJSON]
    View: TypeAlias = Union[tuple[ViewName, Roles], tuple[ViewName, Roles, PostData]]
    ViewKwargs: TypeAlias = dict[str, Union[str, int]]
    ViewGroup: TypeAlias = tuple[list[View], ViewKwargs]
    ViewConfig: TypeAlias = list[ViewGroup]

    ParametrizedView: TypeAlias = tuple[ViewName, ViewKwargs, PostData, Roles]
    ParametrizedViewConfig: TypeAlias = list[ParametrizedView]

    RedirectTarget: TypeAlias = str
    RedirectView: TypeAlias = tuple[ViewNameStr, Roles, RedirectTarget]
    RedirectViewGroup: TypeAlias = tuple[list[RedirectView], ViewKwargs]
    RedirectViewConfig: TypeAlias = list[RedirectViewGroup]

    ParametrizedRedirectView: TypeAlias = tuple[
        ViewName, ViewKwargs, Roles, RedirectTarget
    ]
    ParametrizedRedirectViewConfig: TypeAlias = list[ParametrizedRedirectView]

    ParametrizedPublicView = tuple[ViewNameStr, PostDataDict]
    ParametrizedPublicViewConfig: TypeAlias = list[ParametrizedPublicView]

#: This list contains the config for all views
#: Each element is a tuple which consists of two elements: A list of view configs and the keyword arguments that are
#: identical for all views in this list. Each view config item consists of the name of the view, the list of roles that
#: are allowed to access that view and optionally post data that is sent with the request. The post data can either be
#: a dict to send form data or a string to send JSON.
VIEWS: ViewConfig = [
    (
        [
            ("public:login_webauthn", ALL_ROLES),
            ("sitemap:index", ALL_ROLES),
            ("admin_dashboard", STAFF_ROLES),
            ("admin_feedback", STAFF_ROLES),
            ("languages", STAFF_ROLES),
            ("media_admin", STAFF_ROLES),
            ("mediacenter_directory_path", STAFF_ROLES),
            ("mediacenter_get_directory_content", STAFF_ROLES),
            ("mediacenter_filter_unused_media_files", STAFF_ROLES),
            ("new_language", STAFF_ROLES),
            ("new_offertemplate", STAFF_ROLES),
            ("new_region", STAFF_ROLES),
            ("new_role", [ROOT]),
            ("new_user", STAFF_ROLES),
            ("offertemplates", STAFF_ROLES),
            ("poicategories", STAFF_ROLES),
            ("release_notes", STAFF_ROLES),
            ("regions", STAFF_ROLES),
            ("roles", [ROOT]),
            ("user_settings", STAFF_ROLES),
            (
                "user_settings",
                STAFF_ROLES,
                {
                    "email": "new@email.address",
                    "submit_form": "email_form",
                },
            ),
            (
                "user_settings",
                STAFF_ROLES,
                {
                    "distribute_sidebar_boxes": True,
                    "submit_form": "preferences_form",
                },
            ),
            ("authenticate_modify_mfa", STAFF_ROLES),
            ("users", STAFF_ROLES),
        ],
        # The kwargs for these views
        {},
    ),
    (
        [
            ("dashboard", ROLES),
            ("languagetreenodes", STAFF_ROLES),
            ("media", ROLES),
            ("mediacenter_directory_path", ROLES),
            ("mediacenter_get_directory_content", ROLES),
            ("mediacenter_filter_unused_media_files", ROLES),
            ("new_languagetreenode", STAFF_ROLES),
            (
                "new_languagetreenode",
                HIGH_PRIV_STAFF_ROLES,
                {
                    "language": 5,
                    "parent": 1,
                    "_ref_node_id": 1,
                    "_position": "first-child",
                    "visible": True,
                    "active": True,
                },
            ),
            (
                "bulk_make_languagetreenodes_visible",
                HIGH_PRIV_STAFF_ROLES,
                {"selected_ids[]": [1, 2, 3]},
            ),
            (
                "bulk_hide_languagetreenodes",
                HIGH_PRIV_STAFF_ROLES,
                {"selected_ids[]": [1, 2, 3]},
            ),
            (
                "bulk_activate_languagetreenodes",
                HIGH_PRIV_STAFF_ROLES,
                {"selected_ids[]": [1, 2, 3]},
            ),
            (
                "bulk_disable_languagetreenodes",
                HIGH_PRIV_STAFF_ROLES,
                {"selected_ids[]": [1, 2, 3]},
            ),
            ("new_region_user", STAFF_ROLES + [MANAGEMENT]),
            (
                "new_region_user",
                HIGH_PRIV_STAFF_ROLES + [MANAGEMENT],
                {"username": "new_username", "email": "new@email.address", "role": 1},
            ),
            ("release_notes", ROLES),
            ("region_feedback", STAFF_ROLES + [MANAGEMENT]),
            ("region_users", STAFF_ROLES + [MANAGEMENT]),
            ("translation_coverage", STAFF_ROLES + [MANAGEMENT, EDITOR]),
            ("organizations", STAFF_ROLES + [MANAGEMENT]),
            ("new_organization", STAFF_ROLES + [MANAGEMENT]),
            ("user_settings", ROLES),
            (
                "user_settings",
                ROLES,
                {
                    "email": "new@email.address",
                    "submit_form": "email_form",
                },
            ),
            (
                "user_settings",
                ROLES,
                {
                    "distribute_sidebar_boxes": True,
                    "submit_form": "preferences_form",
                },
            ),
            ("authenticate_modify_mfa", ROLES),
            ("translations_management", HIGH_PRIV_STAFF_ROLES + [MANAGEMENT]),
            (
                "translations_management",
                HIGH_PRIV_STAFF_ROLES + [MANAGEMENT],
                {
                    "machine_translate_pages": 0,
                    "machine_translate_events": 1,
                    "machine_translate_pois": 1,
                },
            ),
            (
                "grant_page_permission_ajax",
                HIGH_PRIV_STAFF_ROLES + [MANAGEMENT],
                json.dumps(
                    {
                        "page_id": 21,
                        "permission": "edit",
                        "user_id": 10,
                    }
                ),
            ),
            (
                "grant_page_permission_ajax",
                HIGH_PRIV_STAFF_ROLES + [MANAGEMENT],
                json.dumps(
                    {
                        "page_id": 21,
                        "permission": "publish",
                        "user_id": 9,
                    }
                ),
            ),
            (
                "revoke_page_permission_ajax",
                HIGH_PRIV_STAFF_ROLES + [MANAGEMENT],
                json.dumps(
                    {
                        "page_id": 5,
                        "permission": "edit",
                        "user_id": 10,
                    }
                ),
            ),
            (
                "revoke_page_permission_ajax",
                HIGH_PRIV_STAFF_ROLES + [MANAGEMENT],
                json.dumps(
                    {
                        "page_id": 6,
                        "permission": "publish",
                        "user_id": 10,
                    }
                ),
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg"},
    ),
    (
        [
            ("dashboard", STAFF_ROLES),
            ("languagetreenodes", STAFF_ROLES),
            ("media", STAFF_ROLES),
            ("mediacenter_directory_path", STAFF_ROLES),
            ("mediacenter_get_directory_content", STAFF_ROLES),
            ("new_languagetreenode", STAFF_ROLES),
            (
                "new_languagetreenode",
                HIGH_PRIV_STAFF_ROLES,
                {
                    "language": 5,
                    "parent": 5,
                    "_ref_node_id": 5,
                    "_position": "first-child",
                    "visible": True,
                    "active": True,
                },
            ),
            ("new_region_user", STAFF_ROLES),
            (
                "new_region_user",
                HIGH_PRIV_STAFF_ROLES,
                {"username": "new_username", "email": "new@email.address", "role": 1},
            ),
            ("region_feedback", STAFF_ROLES),
            ("region_users", STAFF_ROLES),
            ("organizations", STAFF_ROLES),
            ("new_organization", STAFF_ROLES),
            ("translation_coverage", STAFF_ROLES),
            ("user_settings", STAFF_ROLES),
            ("authenticate_modify_mfa", STAFF_ROLES),
        ],
        # The kwargs for these views
        {"region_slug": "nurnberg"},
    ),
    (
        [
            ("dashboard", STAFF_ROLES),
            ("languagetreenodes", STAFF_ROLES),
            ("media", STAFF_ROLES),
            ("mediacenter_directory_path", STAFF_ROLES),
            ("mediacenter_get_directory_content", STAFF_ROLES),
            ("new_region_user", STAFF_ROLES),
            ("region_feedback", STAFF_ROLES),
            ("region_users", STAFF_ROLES),
            ("organizations", STAFF_ROLES),
            ("new_organization", STAFF_ROLES),
            ("translation_coverage", STAFF_ROLES),
            ("user_settings", STAFF_ROLES),
            ("authenticate_modify_mfa", STAFF_ROLES),
        ],
        # The kwargs for these views
        {"region_slug": "empty-region"},
    ),
    (
        [
            ("sitemap:region_language", ALL_ROLES),
            ("archived_pages", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER]),
            ("archived_pois", ROLES),
            ("edit_imprint", STAFF_ROLES + [MANAGEMENT]),
            (
                "edit_imprint",
                PRIV_STAFF_ROLES + [MANAGEMENT],
                {"title": "imprint", "status": status.DRAFT},
            ),
            ("events", ROLES),
            (
                (
                    "events",
                    parse.urlencode(
                        {
                            "events_time_range": "CUSTOM",
                            "date_from": "2023-01-01",
                            "date_to": "2030-12-31",
                        }
                    ),
                ),
                ROLES,
            ),
            (
                (
                    "events",
                    parse.urlencode(
                        {
                            "events_time_range": "CUSTOM",
                            "date_from": "2023-01-01",
                        }
                    ),
                ),
                ROLES,
            ),
            (
                (
                    "events",
                    parse.urlencode(
                        {
                            "events_time_range": "CUSTOM",
                            "date_to": "2030-12-31",
                        }
                    ),
                ),
                ROLES,
            ),
            (
                (
                    "events",
                    parse.urlencode(
                        {
                            "events_time_range": ["PAST", "UPCOMING"],
                        }
                    ),
                ),
                ROLES,
            ),
            (
                (
                    "events",
                    parse.urlencode(
                        {
                            "events_time_range": "UPCOMING",
                            "poi_id": 4,
                            "all_day": 1,
                            "recurring": 1,
                        }
                    ),
                ),
                ROLES,
            ),
            (
                (
                    "events",
                    parse.urlencode(
                        {
                            "events_time_range": "PAST",
                            "all_day": 2,
                            "recurring": 2,
                            "query": "test",
                        }
                    ),
                ),
                ROLES,
            ),
            ("events_archived", ROLES),
            ("new_event", ROLES),
            (
                "new_event",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {
                    "title": "new event",
                    "start_date": "2030-01-01",
                    "end_date": "2030-01-01",
                    "is_all_day": True,
                    "status": status.DRAFT,
                },
            ),
            ("new_page", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER]),
            (
                "new_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {
                    "title": "new page",
                    "mirrored_page_region": "",
                    "_ref_node_id": 1,
                    "_position": "first-child",
                    "status": status.DRAFT,
                },
            ),
            (
                "new_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {
                    "title": "new page",
                    "mirrored_page_region": "",
                    "_ref_node_id": 1,
                    "_position": "first-child",
                    "status": status.PUBLIC,
                },
            ),
            ("new_poi", ROLES),
            (
                "new_poi",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {
                    "title": "new poi",
                    "meta_description": "meta description",
                    "address": "Test-Straße 5",
                    "postcode": "54321",
                    "city": "Augsburg",
                    "country": "Deutschland",
                    "longitude": 1,
                    "latitude": 1,
                    "status": status.DRAFT,
                    "opening_hours": json.dumps(get_default_opening_hours()),
                    "category": 1,
                },
            ),
            ("pages", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER]),
            ("pois", ROLES),
            (
                "bulk_archive_pages",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"selected_ids[]": [1, 2, 3]},
            ),
            (
                "bulk_restore_pages",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"selected_ids[]": [1, 2, 3]},
            ),
            (
                "publish_multiple_pages",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"selected_ids[]": [1]},
            ),
            (
                "draft_multiple_pages",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"selected_ids[]": [1]},
            ),
            (
                "bulk_archive_events",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"selected_ids[]": [1]},
            ),
            (
                "bulk_restore_events",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"selected_ids[]": [1]},
            ),
            (
                "publish_multiple_events",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"selected_ids[]": [1]},
            ),
            (
                "draft_multiple_events",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"selected_ids[]": [1]},
            ),
            (
                "bulk_archive_pois",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"selected_ids[]": [4]},
            ),
            (
                "bulk_restore_pois",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"selected_ids[]": [4]},
            ),
            (
                "publish_multiple_pois",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"selected_ids[]": [4]},
            ),
            (
                "draft_multiple_pois",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"selected_ids[]": [4]},
            ),
            (
                "search_content_ajax",
                ROLES,
                json.dumps(
                    {
                        "query_string": "Test-Veranstaltung",
                        "object_types": ["event"],
                        "archived": False,
                    }
                ),
            ),
            (
                "search_content_ajax",
                ROLES,
                json.dumps(
                    {
                        "query_string": "Test-Ort",
                        "object_types": ["poi"],
                        "archived": False,
                    }
                ),
            ),
            (
                "search_content_ajax",
                STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER],
                json.dumps(
                    {
                        "query_string": "Willkommen",
                        "object_types": ["page"],
                        "archived": False,
                    }
                ),
            ),
            (
                "search_content_ajax",
                STAFF_ROLES + [MANAGEMENT],
                json.dumps(
                    {
                        "query_string": "Test",
                        "object_types": ["feedback"],
                        "archived": False,
                    }
                ),
            ),
            (
                "search_content_ajax",
                STAFF_ROLES + [MANAGEMENT],
                json.dumps(
                    {
                        "query_string": "Test",
                        "object_types": ["push_notification"],
                        "archived": False,
                    }
                ),
            ),
            (
                "search_content_ajax",
                STAFF_ROLES,
                json.dumps(
                    {
                        "query_string": "Augsburg",
                        "object_types": ["region"],
                        "archived": False,
                    }
                ),
            ),
            (
                "search_content_ajax",
                STAFF_ROLES + [MANAGEMENT],
                json.dumps(
                    {
                        "query_string": "root",
                        "object_types": ["user"],
                        "archived": False,
                    }
                ),
            ),
            (
                "search_content_ajax",
                ROLES,
                json.dumps(
                    {
                        "query_string": "Test",
                        "object_types": ["media"],
                        "archived": False,
                    }
                ),
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de"},
    ),
    (
        [
            (
                "slugify_ajax",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                json.dumps(
                    {
                        "title": "Slugify event",
                    }
                ),
            ),
        ],
        {"region_slug": "augsburg", "language_slug": "de", "model_type": "event"},
    ),
    (
        [
            (
                "slugify_ajax",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                json.dumps(
                    {
                        "title": "Slugify poi",
                    }
                ),
            ),
        ],
        {"region_slug": "augsburg", "language_slug": "de", "model_type": "poi"},
    ),
    (
        [
            (
                "slugify_ajax",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                json.dumps(
                    {
                        "title": "Slugify page",
                    }
                ),
            ),
        ],
        {"region_slug": "augsburg", "language_slug": "de", "model_type": "page"},
    ),
    (
        [
            (
                "publish_multiple_pages",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"selected_ids[]": [5]},
            ),
        ],
        {"region_slug": "augsburg", "language_slug": "ar"},
    ),
    (
        [
            ("sbs_edit_imprint", STAFF_ROLES + [MANAGEMENT]),
            (
                "sbs_edit_imprint",
                PRIV_STAFF_ROLES + [MANAGEMENT],
                {"title": "imprint", "status": status.DRAFT},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "en"},
    ),
    (
        [
            (
                "edit_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {
                    "title": "new page",
                    "mirrored_page_region": "",
                    "_ref_node_id": 1,
                    "_position": "first-child",
                    "status": status.PUBLIC,
                },
            ),
        ],
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 4},
    ),
    (
        [
            (
                "edit_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER],
                {
                    "title": "new page",
                    "mirrored_page_region": "",
                    "_ref_node_id": 1,
                    "_position": "first-child",
                    "status": status.REVIEW,
                },
            ),
        ],
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 5},
    ),
    (
        [
            (
                "edit_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, OBSERVER],
                {
                    "title": "new page",
                    "mirrored_page_region": "",
                    "_ref_node_id": 1,
                    "_position": "first-child",
                    "status": status.PUBLIC,
                },
            ),
        ],
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 6},
    ),
    (
        [
            ("archived_pages", STAFF_ROLES),
            ("archived_pois", STAFF_ROLES),
            ("edit_imprint", STAFF_ROLES),
            (
                "edit_imprint",
                PRIV_STAFF_ROLES,
                {"title": "imprint", "status": status.DRAFT},
            ),
            ("events", STAFF_ROLES),
            ("events_archived", STAFF_ROLES),
            ("new_event", STAFF_ROLES),
            (
                "new_event",
                PRIV_STAFF_ROLES,
                {
                    "title": "new event",
                    "start_date": "2030-01-01",
                    "end_date": "2030-01-01",
                    "is_all_day": True,
                    "status": status.DRAFT,
                },
            ),
            ("new_page", STAFF_ROLES),
            (
                "new_page",
                PRIV_STAFF_ROLES,
                {
                    "title": "new page",
                    "mirrored_page_region": "",
                    "_ref_node_id": 7,
                    "_position": "first-child",
                    "status": status.DRAFT,
                },
            ),
            ("new_poi", STAFF_ROLES),
            (
                "new_poi",
                PRIV_STAFF_ROLES,
                {
                    "title": "new poi",
                    "meta_description": "meta description",
                    "address": "Test-Straße 5",
                    "postcode": "54321",
                    "city": "Augsburg",
                    "country": "Deutschland",
                    "longitude": 1,
                    "latitude": 1,
                    "status": status.DRAFT,
                    "opening_hours": json.dumps(get_default_opening_hours()),
                    "category": 1,
                },
            ),
            ("pages", STAFF_ROLES),
            ("pois", STAFF_ROLES),
        ],
        # The kwargs for these views
        {"region_slug": "nurnberg", "language_slug": "de"},
    ),
    (
        [
            ("edit_region", STAFF_ROLES),
            (
                "edit_region",
                PRIV_STAFF_ROLES,
                {
                    "administrative_division": "CITY",
                    "name": "Augsburg",
                    "admin_mail": "augsburg@example.com",
                    "postal_code": "86150",
                    "status": "ACTIVE",
                    "longitude": 1,
                    "latitude": 1,
                    "timezone": "Europe/Berlin",
                    "mt_renewal_month": 6,
                    "offers": [3],
                    "zammad_offers": [5],
                    "zammad_url": "https://zammad-test.example.com",
                },
            ),
            (
                "edit_region",
                PRIV_STAFF_ROLES,
                {
                    "administrative_division": "CITY",
                    "name": "Augsburg",
                    "admin_mail": "augsburg@example.com",
                    "postal_code": "86150",
                    "status": "ARCHIVED",
                    "longitude": 1,
                    "latitude": 1,
                    "timezone": "Europe/Berlin",
                    "mt_renewal_month": 6,
                    "offers": [3],
                    "zammad_offers": [5],
                    "zammad_url": "https://zammad-test.example.com",
                },
            ),
        ],
        # The kwargs for these views
        {"slug": "augsburg"},
    ),
    (
        [
            (
                "delete_region",
                [ROOT, SERVICE_TEAM, CMS_TEAM],
                {
                    "slug": "artland",
                },
            ),
        ],
        {"slug": "artland"},
    ),
    (
        [
            ("edit_language", STAFF_ROLES),
            (
                "edit_language",
                HIGH_PRIV_STAFF_ROLES,
                {
                    "native_name": "New name",
                    "english_name": "German",
                    "slug": "de",
                    "bcp47_tag": "de-de",
                    "text_direction": "LEFT_TO_RIGHT",
                    "table_of_contents": "Inhaltsverzeichnis",
                    "social_media_webapp_title": "Integreat | Web-App | Lokale Informationen für dich",
                    "primary_country_code": "de",
                    "message_content_not_available": "Foo1",
                    "message_partial_live_content_not_available": "Foo2",
                },
            ),
        ],
        # The kwargs for these views
        {"slug": "de"},
    ),
    (
        [("edit_user", STAFF_ROLES)],
        # The kwargs for these views
        {"user_id": 1},
    ),
    (
        [("edit_role", [ROOT])],
        # The kwargs for these views
        {"role_id": 1},
    ),
    (
        [("edit_offertemplate", STAFF_ROLES)],
        # The kwargs for these views
        {"slug": "ihk-lehrstellenboerse"},
    ),
    (
        [("edit_poicategory", STAFF_ROLES)],
        # The kwargs for these views
        {"pk": 1},
    ),
    (
        [
            (
                "edit_poicategory",
                HIGH_PRIV_STAFF_ROLES,
                {
                    "translations-TOTAL_FORMS": 2,
                    "translations-INITIAL_FORMS": 2,
                    "translations-MIN_NUM_FORMS": 2,
                    "translations-MAX_NUM_FORMS": 2,
                    "translations-0-id": 1,
                    "translations-0-category": 1,
                    "translations-0-language": 1,
                    "translations-0-name": "Test Kategorie",
                    "translations-1-id": 2,
                    "translations-1-category": 1,
                    "translations-1-language": 2,
                    "translations-1-name": "Test category",
                },
            )
        ],
        # The kwargs for these views
        {"pk": 1},
    ),
    (
        [("linkcheck", STAFF_ROLES + [MANAGEMENT, EDITOR])],
        # The kwargs for these views
        {"region_slug": "augsburg", "url_filter": "valid"},
    ),
    (
        [("linkcheck", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "url_filter": "valid"},
    ),
    (
        [("linkcheck", STAFF_ROLES + [MANAGEMENT, EDITOR])],
        # The kwargs for these views
        {"region_slug": "augsburg", "url_filter": "unchecked"},
    ),
    (
        [("linkcheck", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "url_filter": "unchecked"},
    ),
    (
        [("linkcheck", STAFF_ROLES + [MANAGEMENT, EDITOR])],
        # The kwargs for these views
        {"region_slug": "augsburg", "url_filter": "ignored"},
    ),
    (
        [("linkcheck", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "url_filter": "ignored"},
    ),
    (
        [("linkcheck", STAFF_ROLES + [MANAGEMENT, EDITOR])],
        # The kwargs for these views
        {"region_slug": "augsburg", "url_filter": "invalid"},
    ),
    (
        [("linkcheck", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "url_filter": "invalid"},
    ),
    (
        [
            (
                "get_page_order_table_ajax",
                STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER],
            )
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "parent_id": 1},
    ),
    (
        [("get_page_order_table_ajax", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "parent_id": 7},
    ),
    (
        [
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 1, "status": status.REVIEW},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 1, "status": status.PUBLIC},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 1, "status": status.DRAFT},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 2, "status": status.PUBLIC},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 1},
    ),
    (
        [
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 1, "status": status.REVIEW},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 1, "status": status.PUBLIC},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 1, "status": status.DRAFT},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 2, "status": status.PUBLIC},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 3},
    ),
    (
        [
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 1, "status": status.REVIEW},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 1, "status": status.PUBLIC},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 1, "status": status.DRAFT},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 2, "status": status.PUBLIC},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 2},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 14},
    ),
    (
        [
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 1, "status": status.REVIEW},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 1, "status": status.PUBLIC},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 1, "status": status.DRAFT},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 2, "status": status.PUBLIC},
            ),
            (
                "page_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 2},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 15},
    ),
    (
        [
            (
                "page_versions",
                # Archived pages should raise PermissionDenied for all roles
                [],
                {"revision": 1, "status": status.PUBLIC},
            )
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 25},
    ),
    (
        [
            (
                "poi_versions",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"revision": 1, "status": status.REVIEW},
            ),
            (
                "poi_versions",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"revision": 1, "status": status.PUBLIC},
            ),
            (
                "poi_versions",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"revision": 1, "status": status.DRAFT},
            ),
            (
                "poi_versions",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"revision": 1},
            ),
            (
                "poi_versions",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"revision": 2, "status": status.PUBLIC},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "poi_id": 4},
    ),
    (
        [
            (
                "event_versions",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"revision": 1, "status": status.REVIEW},
            ),
            (
                "event_versions",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"revision": 1, "status": status.PUBLIC},
            ),
            (
                "event_versions",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"revision": 1, "status": status.DRAFT},
            ),
            (
                "event_versions",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"revision": 1},
            ),
            (
                "event_versions",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"revision": 2, "status": status.PUBLIC},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "event_id": 1},
    ),
    (
        [
            (
                "imprint_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT],
                {"revision": 1, "status": status.REVIEW},
            ),
            (
                "imprint_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT],
                {"revision": 1, "status": status.PUBLIC},
            ),
            (
                "imprint_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT],
                {"revision": 1, "status": status.DRAFT},
            ),
            (
                "imprint_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT],
                {"revision": 1},
            ),
            (
                "imprint_versions",
                PRIV_STAFF_ROLES + [MANAGEMENT],
                {"revision": 2, "status": status.PUBLIC},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de"},
    ),
    (
        [
            (
                "get_page_order_table_ajax",
                STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER],
            )
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "parent_id": 1, "page_id": 2},
    ),
    (
        [("get_page_order_table_ajax", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "parent_id": 7, "page_id": 8},
    ),
    (
        [
            (
                "get_page_order_table_ajax",
                STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER],
            )
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "page_id": 2},
    ),
    (
        [("get_page_order_table_ajax", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "page_id": 8},
    ),
    (
        [
            (
                "get_page_tree_ajax",
                STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER],
                json.dumps([2]),
            )
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de"},
    ),
    (
        [("get_page_tree_ajax", STAFF_ROLES, json.dumps([1]))],
        # The kwargs for these views
        {"region_slug": "nurnberg", "language_slug": "de"},
    ),
    (
        [
            ("edit_page", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER]),
            ("edit_page", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER]),
            (
                "edit_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {
                    "title": "new title",
                    "mirrored_page_region": "",
                    "_ref_node_id": 21,
                    "_position": "first-child",
                    "status": status.REVIEW,
                },
            ),
            (
                "edit_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {
                    "title": "new title",
                    "mirrored_page_region": "",
                    "_ref_node_id": 21,
                    "_position": "first-child",
                    "status": status.DRAFT,
                },
            ),
            (
                "edit_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {
                    "title": "new title",
                    "mirrored_page_region": "",
                    "_ref_node_id": 24,  # Archived ref node
                    "_position": "right",
                    "status": status.DRAFT,
                },
            ),
            (
                "edit_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {
                    "title": "new title",
                    "mirrored_page_region": "",
                    "_ref_node_id": 21,
                    "_position": "first-child",
                    "status": status.PUBLIC,
                },
            ),
            ("sbs_edit_page", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER]),
            ("page_versions", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER]),
            (
                "archive_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"post_data": True},
            ),
            (
                "restore_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"post_data": True},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "en", "page_id": 1},
    ),
    (
        [
            ("edit_page", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER]),
            ("edit_page", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER]),
            (
                "edit_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {
                    "title": "new title",
                    "mirrored_page_region": "",
                    "_ref_node_id": 3,
                    "_position": "first-child",
                    "status": status.REVIEW,
                },
            ),
            (
                "edit_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {
                    "title": "new title",
                    "mirrored_page_region": "",
                    "_ref_node_id": 3,
                    "_position": "first-child",
                    "status": status.DRAFT,
                },
            ),
            (
                "edit_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {
                    "title": "new title",
                    "mirrored_page_region": "",
                    "_ref_node_id": 3,
                    "_position": "first-child",
                    "status": status.PUBLIC,
                },
            ),
            ("sbs_edit_page", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER]),
            ("delete_page", HIGH_PRIV_STAFF_ROLES, {"post_data": True}),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "en", "page_id": 2},
    ),
    (
        [
            ("edit_page", STAFF_ROLES),
            ("sbs_edit_page", STAFF_ROLES),
            ("page_versions", STAFF_ROLES),
            ("archive_page", PRIV_STAFF_ROLES, {"post_data": True}),
            ("restore_page", PRIV_STAFF_ROLES, {"post_data": True}),
        ],
        # The kwargs for these views
        {"region_slug": "nurnberg", "language_slug": "en", "page_id": 7},
    ),
    (
        [
            ("delete_page", HIGH_PRIV_STAFF_ROLES, {"post_data": True}),
        ],
        # The kwargs for these views
        {"region_slug": "nurnberg", "language_slug": "en", "page_id": 8},
    ),
    (
        [
            (
                "move_page",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"post_data": True},
            )
        ],
        # The kwargs for these views
        {
            "region_slug": "augsburg",
            "language_slug": "en",
            "page_id": 1,
            "target_id": 21,
            "position": "first-child",
        },
    ),
    (
        [("page_versions", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER])],
        # The kwargs for these views
        {
            "region_slug": "augsburg",
            "language_slug": "de",
            "page_id": 1,
            "selected_version": 1,
        },
    ),
    (
        [
            ("edit_event", ROLES),
            (
                "edit_event",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {
                    "title": "new title",
                    "start_date": "2030-01-01",
                    "end_date": "2030-01-01",
                    "is_all_day": True,
                    "status": status.DRAFT,
                },
            ),
            (
                "archive_event",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"post_data": True},
            ),
            (
                "restore_event",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"post_data": True},
            ),
            ("delete_event", HIGH_PRIV_STAFF_ROLES, {"post_data": True}),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "event_id": 1},
    ),
    (
        [
            ("edit_poi", ROLES),
            (
                "edit_poi",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {
                    "title": "new title",
                    "meta_description": "meta description",
                    "address": "Test-Straße 5",
                    "postcode": "54321",
                    "city": "Augsburg",
                    "country": "Deutschland",
                    "longitude": 1,
                    "latitude": 1,
                    "status": status.DRAFT,
                    "opening_hours": json.dumps(get_default_opening_hours()),
                    "category": 1,
                },
            ),
            (
                "archive_poi",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"post_data": True},
            ),
            (
                "restore_poi",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"post_data": True},
            ),
            ("delete_poi", HIGH_PRIV_STAFF_ROLES, {"post_data": True}),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "poi_id": 4},
    ),
    (
        [
            ("edit_languagetreenode", STAFF_ROLES),
            (
                "edit_languagetreenode",
                HIGH_PRIV_STAFF_ROLES,
                {
                    "language": 3,
                    "parent": 2,
                    "_ref_node_id": 2,
                    "_position": "first-child",
                },
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "pk": 3},
    ),
    (
        [
            ("edit_region_user", STAFF_ROLES + [MANAGEMENT]),
            (
                "edit_region_user",
                HIGH_PRIV_STAFF_ROLES + [MANAGEMENT],
                {"username": "new_username", "email": "new@email.address", "role": 1},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "user_id": 2},
    ),
    (
        [("edit_region_user", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "user_id": 2},
    ),
    (
        [("dismiss_tutorial", ROLES, {"post_data": True})],
        # The kwargs for these views
        {"region_slug": "augsburg", "slug": "page-tree"},
    ),
    (
        [
            (
                "cancel_translation_process_ajax",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"post_data": True},
            )
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "en", "page_id": 1},
    ),
]

if settings.FCM_ENABLED:
    VIEWS += [
        (
            [
                ("new_push_notification", STAFF_ROLES + [MANAGEMENT]),
                (
                    "new_push_notification",
                    PRIV_STAFF_ROLES + [MANAGEMENT],
                    {
                        "translations-TOTAL_FORMS": 3,
                        "translations-INITIAL_FORMS": 0,
                        "translations-MIN_NUM_FORMS": 1,
                        "translations-MAX_NUM_FORMS": 3,
                        "translations-0-language": 1,
                        "translations-0-title": "Create draft news",
                        "translations-0-text": "Test content",
                        "translations-1-language": 2,
                        "translations-1-title": "test",
                        "translations-1-text": "",
                        "translations-2-language": 5,
                        "translations-2-title": "test",
                        "translations-2-text": "",
                        "regions": [1],
                        "channel": "news",
                        "mode": "ONLY_AVAILABLE",
                        "submit_draft": True,
                    },
                ),
                (
                    "new_push_notification",
                    PRIV_STAFF_ROLES + [MANAGEMENT],
                    {
                        "translations-TOTAL_FORMS": 3,
                        "translations-INITIAL_FORMS": 0,
                        "translations-MIN_NUM_FORMS": 1,
                        "translations-MAX_NUM_FORMS": 3,
                        "translations-0-language": 1,
                        "translations-0-title": "Create scheduled news",
                        "translations-0-text": "Test content",
                        "translations-1-language": 2,
                        "translations-1-title": "test",
                        "translations-1-text": "",
                        "translations-2-language": 5,
                        "translations-2-title": "test",
                        "translations-2-text": "",
                        "regions": [1],
                        "channel": "news",
                        "mode": "ONLY_AVAILABLE",
                        "schedule_send": True,
                        "scheduled_send_date_day": "2040-01-01",
                        "scheduled_send_date_time": "12:00",
                        "submit_schedule": True,
                    },
                ),
                (
                    "new_push_notification",
                    PRIV_STAFF_ROLES + [MANAGEMENT],
                    {
                        "translations-TOTAL_FORMS": 2,
                        "translations-INITIAL_FORMS": 0,
                        "translations-MIN_NUM_FORMS": 1,
                        "translations-MAX_NUM_FORMS": 2,
                        "translations-0-language": 1,
                        "translations-0-title": "Create news template",
                        "translations-0-text": "Test template content",
                        "translations-1-language": 6,
                        "translations-1-title": "",
                        "translations-1-text": "",
                        "regions": [1],
                        "channel": "news",
                        "mode": "USE_MAIN_LANGUAGE",
                        "is_template": True,
                        "template_name": "This is a template",
                        "submit_draft": True,
                    },
                ),
                ("push_notifications", STAFF_ROLES + [MANAGEMENT]),
                ("push_notifications_templates", STAFF_ROLES + [MANAGEMENT]),
            ],
            # The kwargs for these views
            {"region_slug": "augsburg", "language_slug": "de"},
        ),
        (
            [
                (
                    "edit_push_notification",
                    PRIV_STAFF_ROLES + [MANAGEMENT],
                    {
                        "translations-TOTAL_FORMS": 2,
                        "translations-INITIAL_FORMS": 2,
                        "translations-MIN_NUM_FORMS": 2,
                        "translations-MAX_NUM_FORMS": 9,
                        "translations-0-id": 1,
                        "translations-0-language": 1,
                        "translations-0-title": "New unpublish a sent news",
                        "translations-0-text": "New content",
                        "translations-1-id": 2,
                        "translations-1-language": 2,
                        "translations-1-title": "Test EN",
                        "translations-1-text": "Test EN content",
                        "regions": [1],
                        "channel": "news",
                        "mode": "ONLY_AVAILABLE",
                        "submit_draft": True,
                    },
                ),
                (
                    "edit_push_notification",
                    PRIV_STAFF_ROLES + [MANAGEMENT],
                    {
                        "translations-TOTAL_FORMS": 2,
                        "translations-INITIAL_FORMS": 2,
                        "translations-MIN_NUM_FORMS": 2,
                        "translations-MAX_NUM_FORMS": 9,
                        "translations-0-id": 1,
                        "translations-0-language": 1,
                        "translations-0-title": "Test update a sent news",
                        "translations-0-text": "New scheduled content",
                        "translations-1-id": 2,
                        "translations-1-language": 2,
                        "translations-1-title": "Test EN",
                        "translations-1-text": "Test EN content",
                        "regions": [1],
                        "channel": "news",
                        "mode": "ONLY_AVAILABLE",
                        "submit_update": True,
                    },
                ),
            ],
            # The kwargs for these views
            {
                "region_slug": "augsburg",
                "language_slug": "de",
                "push_notification_id": 1,
            },
        ),
        (
            [
                (
                    "edit_push_notification",
                    PRIV_STAFF_ROLES + [MANAGEMENT],
                    {
                        "translations-TOTAL_FORMS": 1,
                        "translations-INITIAL_FORMS": 1,
                        "translations-MIN_NUM_FORMS": 1,
                        "translations-MAX_NUM_FORMS": 9,
                        "translations-0-id": 6,
                        "translations-0-language": 1,
                        "translations-0-title": "Edit existing template",
                        "translations-0-text": "New template content",
                        "regions": [1],
                        "channel": "news",
                        "mode": "ONLY_AVAILABLE",
                        "is_template": True,
                        "template_name": "This is a template",
                        "submit_draft": True,
                    },
                ),
                (
                    "edit_push_notification",
                    PRIV_STAFF_ROLES + [MANAGEMENT],
                    {
                        "translations-TOTAL_FORMS": 1,
                        "translations-INITIAL_FORMS": 1,
                        "translations-MIN_NUM_FORMS": 1,
                        "translations-MAX_NUM_FORMS": 9,
                        "translations-0-id": 6,
                        "translations-0-language": 1,
                        "translations-0-title": "Create news from template",
                        "translations-0-text": "New content",
                        "regions": [1],
                        "channel": "news",
                        "mode": "USE_MAIN_LANGUAGE",
                        "is_template": True,
                        "template_name": "This is a template",
                        "create_from_template": True,
                    },
                ),
            ],
            # The kwargs for these views
            {
                "region_slug": "augsburg",
                "language_slug": "de",
                "push_notification_id": 5,
            },
        ),
        (
            [
                ("new_push_notification", STAFF_ROLES),
                ("push_notifications", STAFF_ROLES),
                ("push_notifications_templates", STAFF_ROLES),
            ],
            # The kwargs for these views
            {"region_slug": "nurnberg", "language_slug": "de"},
        ),
        (
            [
                (
                    "edit_push_notification",
                    PRIV_STAFF_ROLES,
                    {
                        "translations-TOTAL_FORMS": 1,
                        "translations-INITIAL_FORMS": 1,
                        "translations-MIN_NUM_FORMS": 1,
                        "translations-MAX_NUM_FORMS": 9,
                        "translations-0-id": 7,
                        "translations-0-language": 1,
                        "translations-0-title": "Test editing push notification of other region",
                        "translations-0-text": "New template content",
                        "regions": [2],
                        "channel": "news",
                        "mode": "ONLY_AVAILABLE",
                        "submit_draft": True,
                    },
                ),
            ],
            # The kwargs for these views
            {
                "region_slug": "nurnberg",
                "language_slug": "de",
                "push_notification_id": 6,
            },
        ),
    ]

#: In order for these views to be used as parameters, we have to flatten the nested structure
PARAMETRIZED_VIEWS: Final[ParametrizedViewConfig] = [
    (view_name, kwargs, post_data[0] if post_data else {}, roles)
    for view_conf, kwargs in VIEWS
    for view_name, roles, *post_data in view_conf
]

#: This list contains the config for all views which should check whether they correctly redirect to another url
REDIRECT_VIEWS: Final[RedirectViewConfig] = [
    (
        [
            ("public:login", ROLES, settings.LOGIN_REDIRECT_URL),
            ("public:password_reset", ROLES, settings.LOGIN_REDIRECT_URL),
            ("public:wiki_redirect", ALL_ROLES, settings.WIKI_URL),
            ("get_mfa_challenge", STAFF_ROLES, reverse("authenticate_modify_mfa")),
            ("register_new_fido_key", STAFF_ROLES, reverse("authenticate_modify_mfa")),
        ],
        # The kwargs for these views
        {},
    ),
    (
        [
            (
                "statistics",
                STAFF_ROLES + [MANAGEMENT],
                reverse("dashboard", kwargs={"region_slug": "augsburg"}),
            ),
            (
                "get_mfa_challenge",
                ROLES,
                reverse("authenticate_modify_mfa", kwargs={"region_slug": "augsburg"}),
            ),
            (
                "register_new_fido_key",
                ROLES,
                reverse("authenticate_modify_mfa", kwargs={"region_slug": "augsburg"}),
            ),
            (
                "linkcheck_landing",
                STAFF_ROLES + [MANAGEMENT, EDITOR],
                reverse(
                    "linkcheck",
                    kwargs={"region_slug": "augsburg", "url_filter": "invalid"},
                ),
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg"},
    ),
    (
        [
            (
                "pages",
                STAFF_ROLES,
                reverse("languagetreenodes", kwargs={"region_slug": "empty-region"}),
            ),
            (
                "events",
                STAFF_ROLES,
                reverse("languagetreenodes", kwargs={"region_slug": "empty-region"}),
            ),
            (
                "pois",
                STAFF_ROLES,
                reverse("languagetreenodes", kwargs={"region_slug": "empty-region"}),
            ),
            (
                "push_notifications",
                STAFF_ROLES,
                reverse("languagetreenodes", kwargs={"region_slug": "empty-region"}),
            ),
            (
                "edit_imprint",
                STAFF_ROLES,
                reverse("languagetreenodes", kwargs={"region_slug": "empty-region"}),
            ),
        ],
        # The kwargs for these views
        {"region_slug": "empty-region"},
    ),
    (
        [
            (
                "sbs_edit_page",
                STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                reverse(
                    "edit_page",
                    kwargs={
                        "region_slug": "augsburg",
                        "language_slug": "de",
                        "page_id": 1,
                    },
                ),
            )
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 1},
    ),
    (
        [
            (
                "public:expand_page_translation_id",
                ALL_ROLES,
                "https://integreat.app/augsburg/de/willkommen/",
            )
        ],
        # The kwargs for these views
        {"short_url_id": 1},
    ),
    (
        [
            (
                "page_versions",
                ROLES,
                "/augsburg/pages/de/1/versions/",
            ),
        ],
        # The kwargs for these views
        {
            "region_slug": "augsburg",
            "language_slug": "de",
            "page_id": 1,
            "selected_version": 999,
        },
    ),
    (
        [
            (
                "page_versions",
                ROLES,
                "/augsburg/pages/en/2/edit/",
            ),
        ],
        # The kwargs for these views
        {
            "region_slug": "augsburg",
            "language_slug": "en",
            "page_id": 2,
            "selected_version": 1,
        },
    ),
    (
        [
            (
                "event_versions",
                ROLES,
                "/augsburg/events/de/1/versions/",
            ),
        ],
        # The kwargs for these views
        {
            "region_slug": "augsburg",
            "language_slug": "de",
            "event_id": 1,
            "selected_version": 999,
        },
    ),
    (
        [
            (
                "poi_versions",
                ROLES,
                "/augsburg/pois/de/4/versions/",
            ),
        ],
        # The kwargs for these views
        {
            "region_slug": "augsburg",
            "language_slug": "de",
            "poi_id": 4,
            "selected_version": 999,
        },
    ),
    (
        [
            (
                "imprint_versions",
                ROLES,
                "/augsburg/imprint/de/versions/",
            ),
        ],
        # The kwargs for these views
        {
            "region_slug": "augsburg",
            "language_slug": "de",
            "selected_version": 999,
        },
    ),
]

#: In order for these views to be used as parameters, we have to flatten the nested structure
PARAMETRIZED_REDIRECT_VIEWS: Final[ParametrizedRedirectViewConfig] = [
    (view_name, kwargs, roles, target)
    for view_conf, kwargs in REDIRECT_VIEWS
    for view_name, roles, target in view_conf
]

#: Public views that only work for anonymous users
PARAMETRIZED_PUBLIC_VIEWS: Final[ParametrizedPublicViewConfig] = [
    ("public:login", {}),
    ("public:login_webauthn", {}),
    ("public:password_reset", {}),
    ("public:password_reset", {"email": "root@root.root"}),
]
