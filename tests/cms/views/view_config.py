"""
This modules contains the config for the view tests
"""
import json

from django.conf import settings
from django.urls import reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.models.pois.poi import get_default_opening_hours

from ...conftest import (
    ALL_ROLES,
    AUTHOR,
    EDITOR,
    OBSERVER,
    HIGH_PRIV_STAFF_ROLES,
    MANAGEMENT,
    PRIV_STAFF_ROLES,
    WRITE_ROLES,
    ROLES,
    ROOT,
    STAFF_ROLES,
)

#: This list contains the config for all views
#: Each element is a tuple which consists of two elements: A list of view configs and the keyword arguments that are
#: identical for all views in this list. Each view config item consists of the name of the view, the list of roles that
#: are allowed to access that view and optionally post data that is sent with the request. The post data can either be
#: a dict to send form data or a string to send JSON.
VIEWS = [
    (
        [
            ("public:login_mfa", ALL_ROLES),
            ("sitemap:index", ALL_ROLES),
            ("admin_dashboard", STAFF_ROLES),
            ("admin_feedback", STAFF_ROLES),
            ("languages", STAFF_ROLES),
            ("media_admin", STAFF_ROLES),
            ("mediacenter_directory_path", STAFF_ROLES),
            ("mediacenter_get_directory_content", STAFF_ROLES),
            ("new_language", STAFF_ROLES),
            ("new_offertemplate", STAFF_ROLES),
            ("new_region", STAFF_ROLES),
            ("new_role", [ROOT]),
            ("new_user", STAFF_ROLES),
            ("offertemplates", STAFF_ROLES),
            ("poicategories", STAFF_ROLES),
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
                "bulk_archive_pois",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"selected_ids[]": [4]},
            ),
            (
                "bulk_restore_pois",
                PRIV_STAFF_ROLES + WRITE_ROLES,
                {"selected_ids[]": [4]},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de"},
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
                    "deepl_renewal_month": 6,
                },
            ),
        ],
        # The kwargs for these views
        {"slug": "augsburg"},
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
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 1, "status": status.REVIEW},
            ),
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 1, "status": status.PUBLIC},
            ),
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 1, "status": status.DRAFT},
            ),
            (
                "page_revisions",
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
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 1, "status": status.REVIEW},
            ),
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 1, "status": status.PUBLIC},
            ),
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 1, "status": status.DRAFT},
            ),
            (
                "page_revisions",
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
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 1, "status": status.REVIEW},
            ),
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 1, "status": status.PUBLIC},
            ),
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 1, "status": status.DRAFT},
            ),
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 2, "status": status.PUBLIC},
            ),
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 2},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 14},
    ),
    (
        [
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR],
                {"revision": 1, "status": status.REVIEW},
            ),
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 1, "status": status.PUBLIC},
            ),
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 1, "status": status.DRAFT},
            ),
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 2, "status": status.PUBLIC},
            ),
            (
                "page_revisions",
                PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR],
                {"revision": 2},
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 15},
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
        [("get_page_tree_ajax", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER])],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "tree_id": 2},
    ),
    (
        [("get_page_tree_ajax", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "language_slug": "de", "tree_id": 1},
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
            ("page_revisions", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER]),
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
            ("delete_page", HIGH_PRIV_STAFF_ROLES, {"post_data": True}),
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
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "en", "page_id": 2},
    ),
    (
        [
            ("edit_page", STAFF_ROLES),
            ("sbs_edit_page", STAFF_ROLES),
            ("page_revisions", STAFF_ROLES),
            ("archive_page", PRIV_STAFF_ROLES, {"post_data": True}),
            ("restore_page", PRIV_STAFF_ROLES, {"post_data": True}),
            ("delete_page", HIGH_PRIV_STAFF_ROLES, {"post_data": True}),
        ],
        # The kwargs for these views
        {"region_slug": "nurnberg", "language_slug": "en", "page_id": 7},
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
        [("page_revisions", STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER])],
        # The kwargs for these views
        {
            "region_slug": "augsburg",
            "language_slug": "de",
            "page_id": 1,
            "selected_revision": 1,
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
                        "translations-TOTAL_FORMS": 2,
                        "translations-INITIAL_FORMS": 0,
                        "translations-MIN_NUM_FORMS": 1,
                        "translations-MAX_NUM_FORMS": 2,
                        "translations-0-title": "Test title",
                        "translations-0-text": "Test content",
                        "translations-0-language": 1,
                        "translations-1-title": "",
                        "translations-1-text": "",
                        "translations-1-language": 6,
                        "channel": "news",
                        "mode": "ONLY_AVAILABLE",
                    },
                ),
                ("push_notifications", STAFF_ROLES + [MANAGEMENT]),
            ],
            # The kwargs for these views
            {"region_slug": "augsburg", "language_slug": "de"},
        ),
        (
            [
                ("new_push_notification", STAFF_ROLES),
                ("push_notifications", STAFF_ROLES),
            ],
            # The kwargs for these views
            {"region_slug": "nurnberg", "language_slug": "de"},
        ),
    ]

#: In order for these views to be used as parameters, we have to flatten the nested structure
PARAMETRIZED_VIEWS = [
    (view_name, kwargs, post_data[0] if post_data else {}, roles)
    for view_conf, kwargs in VIEWS
    for view_name, roles, *post_data in view_conf
]

#: This list contains the config for all views which should check whether they correctly redirect to another url
REDIRECT_VIEWS = [
    (
        [
            ("public:login", ROLES, settings.LOGIN_REDIRECT_URL),
            ("public:password_reset", ROLES, settings.LOGIN_REDIRECT_URL),
            ("public:wiki_redirect", ALL_ROLES, settings.WIKI_URL),
            ("get_mfa_challenge", STAFF_ROLES, reverse("authenticate_modify_mfa")),
            ("register_new_mfa_key", STAFF_ROLES, reverse("authenticate_modify_mfa")),
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
                "register_new_mfa_key",
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
]

#: In order for these views to be used as parameters, we have to flatten the nested structure
PARAMETRIZED_REDIRECT_VIEWS = [
    (view_name, kwargs, roles, target)
    for view_conf, kwargs in REDIRECT_VIEWS
    for view_name, roles, target in view_conf
]

#: Public views that only work for anonymous users
PARAMETRIZED_PUBLIC_VIEWS = [
    ("public:login", {}),
    ("public:login_mfa", {}),
    ("public:password_reset", {}),
    ("public:password_reset", {"email": "root@root.root"}),
]
