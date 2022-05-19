"""
This modules contains the config for the API tests
"""

#: The API endpoints
API_ENDPOINTS = [
    (
        "/api/regions/",
        "/wp-json/extensions/v3/sites/",
        "tests/api/expected-outputs/regions.json",
        200,
    ),
    (
        "/api/regions/live/",
        "/wp-json/extensions/v3/sites/live/",
        "tests/api/expected-outputs/regions_live.json",
        200,
    ),
    (
        "/api/augsburg/de/pages/",
        "/augsburg/de/wp-json/extensions/v3/pages/",
        "tests/api/expected-outputs/augsburg_de_pages.json",
        200,
    ),
    (
        "/api/augsburg/ar/pages/",
        "/augsburg/ar/wp-json/extensions/v3/pages/",
        "tests/api/expected-outputs/augsburg_ar_pages.json",
        200,
    ),
    (
        "/api/augsburg/non-existing/pages/",
        "/augsburg/non-existing/wp-json/extensions/v3/pages/",
        "tests/api/expected-outputs/augsburg_non-existing_pages.json",
        404,
    ),
    (
        "/api/augsburg/de/locations/",
        "/augsburg/de/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/augsburg_de_locations.json",
        200,
    ),
    (
        "/api/augsburg/en/locations/",
        "/augsburg/en/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/augsburg_en_locations.json",
        200,
    ),
    (
        "/api/augsburg/ar/locations/",
        "/augsburg/ar/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/augsburg_ar_locations.json",
        200,
    ),
    (
        "/api/augsburg/non-existing/locations/",
        "/augsburg/non-existing/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/augsburg_non-existing_locations.json",
        404,
    ),
    (
        "/api/augsburg/de/children/",
        "/augsburg/de/wp-json/extensions/v3/children/",
        "tests/api/expected-outputs/augsburg_de_children.json",
        200,
    ),
    (
        "/api/augsburg/de/children/?depth=3&url=/augsburg/de/behörden-und-beratung/behörden/",
        "/augsburg/de/wp-json/extensions/v3/children/?depth=3&url=/augsburg/de/behörden-und-beratung/behörden/",
        "tests/api/expected-outputs/augsburg_de_children_archived_descendants.json",
        200,
    ),
    (
        "/augsburg/de/wp-json/extensions/v3/page/?url=/augsburg/de/behörden-und-beratung/behörden/archiviertes-amt/",
        "/augsburg/de/wp-json/extensions/v3/page/?url=/augsburg/de/behörden-und-beratung/behörden/archiviertes-amt/",
        "tests/api/expected-outputs/augsburg_de_page_archived.json",
        404,
    ),
    (
        "/api/augsburg/de/children/?depth=2",
        "/augsburg/de/wp-json/extensions/v3/children/?depth=2",
        "tests/api/expected-outputs/api_augsburg_de_children_depth_2.json",
        200,
    ),
    (
        "/api/augsburg/de/events/",
        "/augsburg/de/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/augsburg_de_events.json",
        200,
    ),
    (
        "/api/augsburg/en/events/",
        "/augsburg/en/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/augsburg_en_events.json",
        200,
    ),
    (
        "/api/augsburg/ar/events/",
        "/augsburg/ar/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/augsburg_ar_events.json",
        200,
    ),
    (
        "/api/augsburg/non-existing/events/",
        "/augsburg/non-existing/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/augsburg_non-existing_events.json",
        404,
    ),
    (
        "/api/augsburg/de/page/?id=1",
        "/augsburg/de/wp-json/extensions/v3/page/?id=1",
        "tests/api/expected-outputs/augsburg_de_page_1.json",
        200,
    ),
    (
        "/api/augsburg/de/imprint/",
        "/augsburg/de/wp-json/extensions/v3/disclaimer/",
        "tests/api/expected-outputs/augsburg_de_imprint.json",
        200,
    ),
    (
        "/api/augsburg/en/imprint/",
        "/augsburg/en/wp-json/extensions/v3/disclaimer/",
        "tests/api/expected-outputs/augsburg_en_imprint.json",
        200,
    ),
    (
        "/api/augsburg/non-existing/imprint/",
        "/augsburg/non-existing/wp-json/extensions/v3/disclaimer/",
        "tests/api/expected-outputs/augsburg_non-existing_imprint.json",
        404,
    ),
    (
        "/api/nurnberg/de/events/",
        "/nurnberg/de/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/nurnberg_de_events.json",
        200,
    ),
    (
        "/api/nurnberg/en/events/",
        "/nurnberg/en/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/nurnberg_en_events.json",
        200,
    ),
    (
        "/api/nurnberg/ar/events/",
        "/nurnberg/ar/wp-json/extensions/v3/events/",
        "tests/api/expected-outputs/nurnberg_ar_events.json",
        200,
    ),
    (
        "/api/nurnberg/de/locations/",
        "/nurnberg/de/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/nurnberg_de_locations.json",
        200,
    ),
    (
        "/api/nurnberg/en/locations/",
        "/nurnberg/en/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/nurnberg_en_locations.json",
        200,
    ),
    (
        "/api/nurnberg/ar/locations/",
        "/nurnberg/ar/wp-json/extensions/v3/locations/",
        "tests/api/expected-outputs/nurnberg_ar_locations.json",
        200,
    ),
    (
        "/api/nurnberg/de/imprint/",
        "/nurnberg/de/wp-json/extensions/v3/disclaimer/",
        "tests/api/expected-outputs/nurnberg_de_imprint.json",
        200,
    ),
    (
        "/api/nurnberg/en/imprint/",
        "/nurnberg/en/wp-json/extensions/v3/disclaimer/",
        "tests/api/expected-outputs/nurnberg_en_imprint.json",
        200,
    ),
    (
        "/api/nurnberg/de/fcm/",
        "/nurnberg/de/wp-json/extensions/v3/fcm/",
        "tests/api/expected-outputs/nurnberg_de_fcm.json",
        200,
    ),
    (
        "/api/nurnberg/en/fcm/",
        "/nurnberg/en/wp-json/extensions/v3/fcm/",
        "tests/api/expected-outputs/nurnberg_en_fcm.json",
        200,
    ),
    (
        "/api/nurnberg/ar/fcm/",
        "/nurnberg/ar/wp-json/extensions/v3/fcm/",
        "tests/api/expected-outputs/nurnberg_ar_fcm.json",
        200,
    ),
    (
        "/api/augsburg/de/extras/",
        "/augsburg/de/wp-json/extensions/v3/extras/",
        "tests/api/expected-outputs/augsburg-offers.json",
        200,
    ),
]

#: This list contains the config for all API feedback views
API_FEEDBACK_VIEWS = [
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
        {"comment": "Cool region!", "rating": "up", "category": "Inhalte"},
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
            "slug": "test-veranstaltung",
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
