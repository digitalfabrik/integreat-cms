"""
This modules contains the config for the API tests
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final

#: The API endpoints
API_ENDPOINTS: Final[list[tuple[str, str, str, int, int]]] = [
    (
        "/api/v3/regions/",
        "/wp-json/extensions/v3/sites/",
        "tests/api/expected-outputs/regions.json",
        200,
        7,
    ),
    (
        "/api/v3/regions/augsburg/",
        "/wp-json/extensions/v3/sites/augsburg/",
        "tests/api/expected-outputs/regions_augsburg.json",
        200,
        3,
    ),
    (
        "/api/v3/regions/nurnberg/",
        "/wp-json/extensions/v3/sites/nurnberg/",
        "tests/api/expected-outputs/regions_nurnberg.json",
        200,
        3,
    ),
    (
        "/api/v3/augsburg/languages/",
        "/augsburg/de/wp-json/extensions/v3/languages/",
        "tests/api/expected-outputs/augsburg_languages.json",
        200,
        2,
    ),
    (
        "/api/v3/nurnberg/languages/",
        "/nurnberg/de/wp-json/extensions/v3/languages/",
        "tests/api/expected-outputs/nurnberg_languages.json",
        200,
        2,
    ),
    (
        "/api/v3/augsburg/de/pages/",
        "/augsburg/de/wp-json/extensions/v3/pages/",
        "tests/api/expected-outputs/augsburg_de_pages.json",
        200,
        6,
    ),
    (
        "/api/v3/augsburg/ar/pages/",
        "/augsburg/ar/wp-json/extensions/v3/pages/",
        "tests/api/expected-outputs/augsburg_ar_pages.json",
        200,
        6,
    ),
    (
        "/api/v3/augsburg/non-existing/pages/",
        "/augsburg/non-existing/wp-json/extensions/v3/pages/",
        "tests/api/expected-outputs/augsburg_non-existing_pages.json",
        404,
        2,
    ),
    (
        "/api/v3/augsburg/de/locations/",
        "/augsburg/de/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/augsburg_de_locations.json",
        200,
        5,
    ),
    (
        "/api/v3/augsburg/en/locations/",
        "/augsburg/en/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/augsburg_en_locations.json",
        200,
        5,
    ),
    (
        "/api/v3/augsburg/ar/locations/",
        "/augsburg/ar/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/augsburg_ar_locations.json",
        200,
        5,
    ),
    (
        "/api/v3/augsburg/non-existing/locations/",
        "/augsburg/non-existing/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/augsburg_non-existing_locations.json",
        404,
        2,
    ),
    (
        "/api/v3/augsburg/de/location-categories/",
        "/augsburg/de/wp-json/extensions/v3/location-categories/",
        "tests/api/expected-outputs/augsburg_de_location_categories.json",
        200,
        12,
    ),
    (
        "/api/v3/augsburg/en/location-categories/",
        "/augsburg/en/wp-json/extensions/v3/location-categories/",
        "tests/api/expected-outputs/augsburg_en_location_categories.json",
        200,
        12,
    ),
    (
        "/api/v3/augsburg/ar/location-categories/",
        "/augsburg/ar/wp-json/extensions/v3/location-categories/",
        "tests/api/expected-outputs/augsburg_ar_location_categories.json",
        200,
        12,
    ),
    (
        "/api/v3/augsburg/de/children/",
        "/augsburg/de/wp-json/extensions/v3/children/",
        "tests/api/expected-outputs/augsburg_de_children.json",
        200,
        13,
    ),
    (
        "/api/v3/augsburg/de/children/?depth=3&url=/augsburg/de/behörden-und-beratung/behörden/",
        "/augsburg/de/wp-json/extensions/v3/children/?depth=3&url=/augsburg/de/behörden-und-beratung/behörden/",
        "tests/api/expected-outputs/augsburg_de_children_archived_descendants.json",
        200,
        14,
    ),
    (
        "/augsburg/de/wp-json/extensions/v3/page/?url=/augsburg/de/behörden-und-beratung/behörden/archiviertes-amt/",
        "/augsburg/de/wp-json/extensions/v3/page/?url=/augsburg/de/behörden-und-beratung/behörden/archiviertes-amt/",
        "tests/api/expected-outputs/augsburg_de_page_archived.json",
        404,
        4,
    ),
    (
        "/api/v3/augsburg/de/children/?depth=2",
        "/augsburg/de/wp-json/extensions/v3/children/?depth=2",
        "tests/api/expected-outputs/augsburg_de_children_depth_2.json",
        200,
        13,
    ),
    (
        "/api/v3/augsburg/de/events/",
        "/augsburg/de/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/augsburg_de_events.json",
        200,
        5,
    ),
    (
        "/api/v3/augsburg/de/events/?combine_recurring=True",
        "/augsburg/de/wp-json/extensions/v3/events/?combine_recurring=True",
        "tests/api/expected-outputs/augsburg_de_events_combine_recurring.json",
        200,
        5,
    ),
    (
        "/api/v3/augsburg/en/events/",
        "/augsburg/en/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/augsburg_en_events.json",
        200,
        5,
    ),
    (
        "/api/v3/augsburg/ar/events/",
        "/augsburg/ar/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/augsburg_ar_events.json",
        200,
        5,
    ),
    (
        "/api/v3/augsburg/non-existing/events/",
        "/augsburg/non-existing/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/augsburg_non-existing_events.json",
        404,
        2,
    ),
    (
        "/api/v3/augsburg/de/page/?id=1",
        "/augsburg/de/wp-json/extensions/v3/page/?id=1",
        "tests/api/expected-outputs/augsburg_de_page_1.json",
        200,
        5,
    ),
    (
        "/api/v3/augsburg/de/imprint/",
        "/augsburg/de/wp-json/extensions/v3/disclaimer/",
        "tests/api/expected-outputs/augsburg_de_imprint.json",
        200,
        4,
    ),
    (
        "/api/v3/augsburg/en/imprint/",
        "/augsburg/en/wp-json/extensions/v3/disclaimer/",
        "tests/api/expected-outputs/augsburg_en_imprint.json",
        200,
        4,
    ),
    (
        "/api/v3/augsburg/non-existing/imprint/",
        "/augsburg/non-existing/wp-json/extensions/v3/disclaimer/",
        "tests/api/expected-outputs/augsburg_non-existing_imprint.json",
        404,
        2,
    ),
    (
        "/api/v3/nurnberg/de/events/",
        "/nurnberg/de/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/nurnberg_de_events.json",
        200,
        9,
    ),
    (
        "/api/v3/nurnberg/en/events/",
        "/nurnberg/en/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/nurnberg_en_events.json",
        200,
        9,
    ),
    (
        "/api/v3/nurnberg/ar/events/",
        "/nurnberg/ar/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/nurnberg_ar_events.json",
        200,
        5,
    ),
    (
        "/api/v3/nurnberg/de/locations/",
        "/nurnberg/de/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/nurnberg_de_locations.json",
        200,
        5,
    ),
    (
        "/api/v3/nurnberg/en/locations/",
        "/nurnberg/en/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/nurnberg_en_locations.json",
        200,
        5,
    ),
    (
        "/api/v3/nurnberg/ar/locations/",
        "/nurnberg/ar/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/nurnberg_ar_locations.json",
        200,
        5,
    ),
    (
        "/api/v3/nurnberg/de/imprint/",
        "/nurnberg/de/wp-json/extensions/v3/disclaimer/",
        "tests/api/expected-outputs/nurnberg_de_imprint.json",
        200,
        3,
    ),
    (
        "/api/v3/nurnberg/en/imprint/",
        "/nurnberg/en/wp-json/extensions/v3/disclaimer/",
        "tests/api/expected-outputs/nurnberg_en_imprint.json",
        200,
        3,
    ),
    (
        "/api/v3/nurnberg/de/fcm/",
        "/nurnberg/de/wp-json/extensions/v3/fcm/",
        "tests/api/expected-outputs/nurnberg_de_fcm.json",
        200,
        3,
    ),
    (
        "/api/v3/nurnberg/en/fcm/",
        "/nurnberg/en/wp-json/extensions/v3/fcm/",
        "tests/api/expected-outputs/nurnberg_en_fcm.json",
        200,
        3,
    ),
    (
        "/api/v3/nurnberg/ar/fcm/",
        "/nurnberg/ar/wp-json/extensions/v3/fcm/",
        "tests/api/expected-outputs/nurnberg_ar_fcm.json",
        200,
        3,
    ),
    (
        "/api/v3/augsburg/de/extras/",
        "/augsburg/de/wp-json/extensions/v3/extras/",
        "tests/api/expected-outputs/augsburg-offers.json",
        200,
        3,
    ),
]

#: This list contains the config for all API feedback views
API_FEEDBACK_VIEWS: Final[list[tuple[str, dict[str, str]]]] = [
    (
        "api:legacy_feedback_endpoint",
        {
            "permalink": "/augsburg/de/willkommen",
            "comment": "Cool page!",
            "rating": "up",
            "category": "Inhalte",
        },
    ),
    (
        "api:legacy_feedback_endpoint",
        {
            "permalink": "/augsburg/de/willkommen",
            "comment": "Strange bug!",
            "rating": "down",
            "category": "Technisches Feedback",
        },
    ),
    (
        "api:legacy_feedback_endpoint",
        {
            "permalink": "/augsburg/de/events/test-veranstaltung",
            "comment": "Cool event!",
            "rating": "up",
            "category": "Inhalte",
        },
    ),
    (
        "api:legacy_feedback_endpoint",
        {
            "permalink": "/augsburg/de/events/test-veranstaltung",
            "comment": "Strange bug!",
            "rating": "down",
            "category": "Technisches Feedback",
        },
    ),
    (
        "api:region_feedback",
        {"rating": "up", "category": "Inhalte"},
    ),
    (
        "api:region_feedback",
        {"comment": "Feedback ohne Bewertung", "category": "Inhalte"},
    ),
    (
        "api:region_feedback",
        {
            "comment": "Strange bug!",
            "rating": "down",
            "category": "Technisches Feedback",
        },
    ),
    (
        "api:page_feedback",
        {
            "slug": "willkommen",
            "comment": "Cool page!",
            "rating": "up",
            "category": "Inhalte",
        },
    ),
    (
        "api:page_feedback",
        {
            "slug": "willkommen",
            "comment": "Strange bug!",
            "rating": "down",
            "category": "Technisches Feedback",
        },
    ),
    (
        "api:poi_feedback",
        {
            "slug": "test-ort",
            "comment": "Cool POI!",
            "rating": "up",
            "category": "Inhalte",
        },
    ),
    (
        "api:poi_feedback",
        {
            "slug": "test-ort",
            "comment": "Strange bug!",
            "rating": "down",
            "category": "Technisches Feedback",
        },
    ),
    (
        "api:event_feedback",
        {
            "slug": "test-veranstaltung",
            "comment": "Cool event!",
            "rating": "up",
            "category": "Inhalte",
        },
    ),
    (
        "api:event_feedback",
        {
            "slug": "test-veranstaltung$2030-01-01",
            "comment": "Strange bug!",
            "rating": "down",
            "category": "Technisches Feedback",
        },
    ),
    (
        "api:event_list_feedback",
        {"comment": "Cool events!", "rating": "up", "category": "Inhalte"},
    ),
    (
        "api:event_list_feedback",
        {
            "comment": "Strange bug!",
            "rating": "down",
            "category": "Technisches Feedback",
        },
    ),
    (
        "api:imprint_page_feedbacks",
        {"comment": "Cool imprint!", "rating": "up", "category": "Inhalte"},
    ),
    (
        "api:imprint_page_feedbacks",
        {
            "comment": "Strange bug!",
            "rating": "down",
            "category": "Technisches Feedback",
        },
    ),
    (
        "api:map_feedback",
        {"comment": "Cool map!", "rating": "up", "category": "Inhalte"},
    ),
    (
        "api:map_feedback",
        {
            "comment": "Strange bug!",
            "rating": "down",
            "category": "Technisches Feedback",
        },
    ),
    (
        "api:search_result_feedback",
        {
            "query": "search query",
            "comment": "Cool search results!",
            "rating": "up",
            "category": "Inhalte",
        },
    ),
    (
        "api:search_result_feedback",
        {
            "query": "search query",
            "comment": "Strange bug!",
            "rating": "down",
            "category": "Technisches Feedback",
        },
    ),
    (
        "api:offer_list_feedback",
        {"comment": "Cool offers!", "rating": "up", "category": "Inhalte"},
    ),
    (
        "api:offer_list_feedback",
        {
            "comment": "Strange bug!",
            "rating": "down",
            "category": "Technisches Feedback",
        },
    ),
    (
        "api:offer_feedback",
        {
            "slug": "sprungbrett",
            "comment": "Cool offer!",
            "rating": "up",
            "category": "Inhalte",
        },
    ),
    (
        "api:offer_feedback",
        {
            "slug": "sprungbrett",
            "comment": "Strange bug!",
            "rating": "down",
            "category": "Technisches Feedback",
        },
    ),
]

API_FEEDBACK_ERRORS: Final[
    list[tuple[str, dict[str, str], dict[str, str], dict[str, int | str]]]
] = [
    (
        "api:region_feedback",
        {"region_slug": "augsburg", "language_slug": "ch"},
        {"rating": "up"},
        {"code": 404, "error": 'No language found with slug "ch"'},
    ),
    (
        "api:region_feedback",
        {"region_slug": "augsburg", "language_slug": "de"},
        {"rating": "neutral"},
        {"code": 400, "error": "Invalid rating."},
    ),
    (
        "api:region_feedback",
        {"region_slug": "augsburg", "language_slug": "de"},
        {"category": "Inhalte"},
        {"code": 400, "error": "Either comment or rating is required."},
    ),
    (
        "api:event_feedback",
        {"region_slug": "augsburg", "language_slug": "de"},
        {"slug": "not-exist", "rating": "down"},
        {"code": 404, "error": "No matching event found for slug."},
    ),
    (
        "api:page_feedback",
        {"region_slug": "augsburg", "language_slug": "de"},
        {"slug": "not-exist", "rating": "down"},
        {"code": 404, "error": "No matching page found for slug."},
    ),
    (
        "api:poi_feedback",
        {"region_slug": "augsburg", "language_slug": "de"},
        {"slug": "not-exist", "rating": "down"},
        {"code": 404, "error": "No matching location found for slug."},
    ),
    (
        "api:imprint_page_feedbacks",
        {"region_slug": "nurnberg", "language_slug": "de"},
        {"rating": "down"},
        {
            "code": 404,
            "error": "The imprint does not exist in this region for the selected language.",
        },
    ),
    (
        "api:search_result_feedback",
        {"region_slug": "augsburg", "language_slug": "de"},
        {"rating": "down"},
        {"code": 400, "error": "Search query is required."},
    ),
]

API_SOCIAL_ENDPOINTS: Final[list[tuple[str, str, str, int, int]]] = [
    (
        "/api/social/",
        "/wp-json/extensions/v3/social/",
        "tests/api/expected-outputs/root_de_social.json",
        200,
        1,
    ),
    (
        "/api/social/landing/en/",
        "/wp-json/extensions/v3/social/landing/en/",
        "tests/api/expected-outputs/root_en_social.json",
        200,
        2,
    ),
    (
        "/api/social/augsburg/de/",
        "/wp-json/extensions/v3/social/augsburg/de/",
        "tests/api/expected-outputs/augsburg_de_social.json",
        200,
        3,
    ),
    (
        "/api/social/augsburg/de/willkommen/",
        "/wp-json/extensions/v3/social/augsburg/de/willkommen/",
        "tests/api/expected-outputs/augsburg_de_social_page.json",
        200,
        7,
    ),
    (
        "/api/social/augsburg/de/non-existing/",
        "/wp-json/extensions/v3/social/augsburg/de/non-existing/",
        "tests/api/expected-outputs/augsburg_de_social_non-existing_page.json",
        200,
        4,
    ),
    (
        "/api/social/augsburg/de/non-existing/",
        "/wp-json/extensions/v3/social/augsburg/de/non-existing/",
        "tests/api/expected-outputs/augsburg_de_social_non-existing_page.json",
        200,
        4,
    ),
    (
        "/api/social/augsburg/de/events/test-veranstaltung/",
        "/wp-json/extensions/v3/social/augsburg/de/events/test-veranstaltung/",
        "tests/api/expected-outputs/augsburg_de_social_event.json",
        200,
        7,
    ),
    (
        "/api/social/augsburg/de/locations/test-ort/",
        "/wp-json/extensions/v3/social/augsburg/de/locations/test-ort/",
        "tests/api/expected-outputs/augsburg_de_social_location.json",
        200,
        7,
    ),
    (
        "/api/social/augsburg/de/news/local/1/",
        "/wp-json/extensions/v3/social/augsburg/de/news/local/1/",
        "tests/api/expected-outputs/augsburg_de_social_location.json",
        200,
        8,
    ),
]
