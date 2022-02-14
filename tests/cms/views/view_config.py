"""
This modules contains the config for the view tests
"""

from django.conf import settings
from django.urls import reverse

from ...conftest import (
    MANAGEMENT,
    EDITOR,
    STAFF_ROLES,
    ALL_ROLES,
    ROLES,
    ROOT,
)

#: This list contains the config for all views
VIEWS = [
    (
        [
            ("api:regions", ALL_ROLES),
            ("api:regions_live", ALL_ROLES),
            ("api:regions_hidden", ALL_ROLES),
            ("public:login_mfa", ALL_ROLES),
            ("admin_dashboard", STAFF_ROLES),
            ("admin_feedback", STAFF_ROLES),
            ("languages", STAFF_ROLES),
            ("media_admin", STAFF_ROLES),
            ("mediacenter_directory_path", STAFF_ROLES),
            ("mediacenter_get_directory_content", STAFF_ROLES),
            ("new_language", STAFF_ROLES),
            ("new_offertemplate", STAFF_ROLES),
            ("new_organization", STAFF_ROLES),
            ("new_region", STAFF_ROLES),
            ("new_role", [ROOT]),
            ("new_user", STAFF_ROLES),
            ("offertemplates", STAFF_ROLES),
            ("organizations", STAFF_ROLES),
            ("regions", STAFF_ROLES),
            ("roles", [ROOT]),
            ("user_settings", STAFF_ROLES),
            ("authenticate_modify_mfa", STAFF_ROLES),
            ("users", STAFF_ROLES),
        ],
        # The kwargs for these views
        {},
    ),
    (
        [
            ("api:languages", ALL_ROLES),
            ("analytics", ROLES),
            ("app_size", ROLES),
            ("dashboard", ROLES),
            ("language_tree", STAFF_ROLES),
            ("media", ROLES),
            ("mediacenter_directory_path", ROLES),
            ("mediacenter_get_directory_content", ROLES),
            ("new_language_tree_node", STAFF_ROLES),
            ("new_region_user", STAFF_ROLES + [MANAGEMENT]),
            ("region_feedback", ROLES),
            ("region_users", STAFF_ROLES + [MANAGEMENT]),
            ("translation_coverage", ROLES),
            ("user_settings", ROLES),
            ("authenticate_modify_mfa", ROLES),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg"},
    ),
    (
        [
            ("api:languages", ALL_ROLES),
            ("analytics", STAFF_ROLES),
            ("app_size", STAFF_ROLES),
            ("dashboard", STAFF_ROLES),
            ("language_tree", STAFF_ROLES),
            ("media", STAFF_ROLES),
            ("mediacenter_directory_path", STAFF_ROLES),
            ("mediacenter_get_directory_content", STAFF_ROLES),
            ("new_language_tree_node", STAFF_ROLES),
            ("new_region_user", STAFF_ROLES),
            ("region_feedback", STAFF_ROLES),
            ("region_users", STAFF_ROLES),
            ("translation_coverage", STAFF_ROLES),
            ("user_settings", STAFF_ROLES),
            ("authenticate_modify_mfa", STAFF_ROLES),
        ],
        # The kwargs for these views
        {"region_slug": "nurnberg"},
    ),
    (
        [
            ("api:pages", ALL_ROLES),
            ("api:pdf_export", ALL_ROLES),
            ("api:sent_push_notifications", ALL_ROLES),
            ("archived_pages", STAFF_ROLES + [MANAGEMENT, EDITOR]),
            ("archived_pois", ROLES),
            ("edit_imprint", ROLES),
            ("events", ROLES),
            ("events_archived", ROLES),
            ("new_event", ROLES),
            ("new_page", STAFF_ROLES + [MANAGEMENT, EDITOR]),
            ("new_poi", ROLES),
            ("new_push_notification", STAFF_ROLES + [MANAGEMENT]),
            ("pages", STAFF_ROLES + [MANAGEMENT, EDITOR]),
            ("pois", ROLES),
            ("push_notifications", STAFF_ROLES + [MANAGEMENT]),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de"},
    ),
    (
        [
            ("api:pages", ALL_ROLES),
            ("api:pdf_export", ALL_ROLES),
            ("api:sent_push_notifications", ALL_ROLES),
            ("archived_pages", STAFF_ROLES),
            ("archived_pois", STAFF_ROLES),
            ("edit_imprint", STAFF_ROLES),
            ("events", STAFF_ROLES),
            ("events_archived", STAFF_ROLES),
            ("new_event", STAFF_ROLES),
            ("new_page", STAFF_ROLES),
            ("new_poi", STAFF_ROLES),
            ("new_push_notification", STAFF_ROLES),
            ("pages", STAFF_ROLES),
            ("pois", STAFF_ROLES),
            ("push_notifications", STAFF_ROLES),
        ],
        # The kwargs for these views
        {"region_slug": "nurnberg", "language_slug": "de"},
    ),
    (
        [("edit_region", STAFF_ROLES)],
        # The kwargs for these views
        {"slug": "augsburg"},
    ),
    (
        [("edit_language", STAFF_ROLES)],
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
        [("linkcheck", ROLES)],
        # The kwargs for these views
        {"region_slug": "augsburg", "link_filter": "valid"},
    ),
    (
        [("linkcheck", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "link_filter": "valid"},
    ),
    (
        [("linkcheck", ROLES)],
        # The kwargs for these views
        {"region_slug": "augsburg", "link_filter": "unchecked"},
    ),
    (
        [("linkcheck", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "link_filter": "unchecked"},
    ),
    (
        [("linkcheck", ROLES)],
        # The kwargs for these views
        {"region_slug": "augsburg", "link_filter": "ignored"},
    ),
    (
        [("linkcheck", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "link_filter": "ignored"},
    ),
    (
        [("linkcheck", ROLES)],
        # The kwargs for these views
        {"region_slug": "augsburg", "link_filter": "invalid"},
    ),
    (
        [("linkcheck", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "link_filter": "invalid"},
    ),
    (
        [("get_new_page_order_table_ajax", STAFF_ROLES + [MANAGEMENT, EDITOR])],
        # The kwargs for these views
        {"region_slug": "augsburg", "parent_id": 1},
    ),
    (
        [("get_new_page_order_table_ajax", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "parent_id": 7},
    ),
    (
        [("get_page_order_table_ajax", STAFF_ROLES + [MANAGEMENT, EDITOR])],
        # The kwargs for these views
        {"region_slug": "augsburg", "parent_id": 1, "page_id": 2},
    ),
    (
        [("get_page_order_table_ajax", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "parent_id": 7, "page_id": 8},
    ),
    (
        [("get_page_children_ajax", STAFF_ROLES + [MANAGEMENT, EDITOR])],
        # The kwargs for these views
        {
            "region_slug": "augsburg",
            "language_slug": "de",
            "tree_id": 2,
            "lft": 1,
            "rgt": 12,
            "depth": 1,
        },
    ),
    (
        [("get_page_children_ajax", STAFF_ROLES)],
        # The kwargs for these views
        {
            "region_slug": "nurnberg",
            "language_slug": "de",
            "tree_id": 1,
            "lft": 1,
            "rgt": 14,
            "depth": 1,
        },
    ),
    (
        [
            ("view_page", STAFF_ROLES + [MANAGEMENT, EDITOR]),
            ("edit_page", STAFF_ROLES + [MANAGEMENT, EDITOR]),
            ("sbs_edit_page", STAFF_ROLES + [MANAGEMENT, EDITOR]),
            ("page_revisions", STAFF_ROLES + [MANAGEMENT, EDITOR]),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "en", "page_id": 1},
    ),
    (
        [
            ("view_page", STAFF_ROLES),
            ("edit_page", STAFF_ROLES),
            ("sbs_edit_page", STAFF_ROLES),
            ("page_revisions", STAFF_ROLES),
        ],
        # The kwargs for these views
        {"region_slug": "nurnberg", "language_slug": "en", "page_id": 7},
    ),
    (
        [("page_revisions", STAFF_ROLES + [MANAGEMENT, EDITOR])],
        # The kwargs for these views
        {
            "region_slug": "augsburg",
            "language_slug": "de",
            "page_id": 1,
            "selected_revision": 1,
        },
    ),
    (
        [("edit_event", ROLES)],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "event_id": 1},
    ),
    (
        [("edit_poi", ROLES)],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "poi_id": 1},
    ),
    (
        [("edit_language_tree_node", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_tree_node_id": 1},
    ),
    (
        [("edit_language_tree_node", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "language_tree_node_id": 5},
    ),
    (
        [("edit_region_user", STAFF_ROLES + [MANAGEMENT])],
        # The kwargs for these views
        {"region_slug": "augsburg", "user_id": 2},
    ),
    (
        [("edit_region_user", STAFF_ROLES)],
        # The kwargs for these views
        {"region_slug": "nurnberg", "user_id": 2},
    ),
]

#: In order for these views to be used as parameters, we have to flatten the nested structure
PARAMETRIZED_VIEWS = [
    (view_name, kwargs, roles)
    for view_conf, kwargs in VIEWS
    for view_name, roles in view_conf
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
                ROLES,
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
                STAFF_ROLES,
                reverse(
                    "linkcheck",
                    kwargs={"region_slug": "augsburg", "link_filter": "invalid"},
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
                STAFF_ROLES + [MANAGEMENT, EDITOR],
                reverse(
                    "edit_page",
                    kwargs={
                        "region_slug": "augsburg",
                        "language_slug": "de",
                        "page_id": 1,
                    },
                ),
            ),
        ],
        # The kwargs for these views
        {"region_slug": "augsburg", "language_slug": "de", "page_id": 1},
    ),
]

#: In order for these views to be used as parameters, we have to flatten the nested structure
PARAMETRIZED_REDIRECT_VIEWS = [
    (view_name, kwargs, roles, target)
    for view_conf, kwargs in REDIRECT_VIEWS
    for view_name, roles, target in view_conf
]
