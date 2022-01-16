from django.test import TestCase
from linkcheck.listeners import disable_listeners
from .api_tests_utils import generate_test_functions

endpoint_data = [
    (
        "/api/regions/",
        "/wp-json/extensions/v3/sites/",
        "integreat_cms/api/tests/expected-outputs/regions.json",
    ),
    (
        "/api/regions/live",
        "/wp-json/extensions/v3/sites/live",
        "integreat_cms/api/tests/expected-outputs/regions_live.json",
    ),
    (
        "/api/augsburg/de/pages",
        "/augsburg/de/wp-json/extensions/v3/pages",
        "integreat_cms/api/tests/expected-outputs/augsburg_de_pages.json",
    ),
    (
        "/api/augsburg/de/locations",
        "/augsburg/de/wp-json/extensions/v3/locations",
        "integreat_cms/api/tests/expected-outputs/augsburg_de_locations.json",
    ),
    (
        "/api/augsburg/de/children",
        "/augsburg/de/wp-json/extensions/v3/children",
        "integreat_cms/api/tests/expected-outputs/augsburg_de_children.json",
    ),
    (
        "/api/augsburg/de/children?depth=2",
        "/augsburg/de/wp-json/extensions/v3/children?depth=2",
        "integreat_cms/api/tests/expected-outputs/api_augsburg_de_children_depth_2.json",
    ),
    (
        "/api/augsburg/de/events",
        "/augsburg/de/wp-json/extensions/v3/events",
        "integreat_cms/api/tests/expected-outputs/augsburg_de_events.json",
    ),
    (
        "/api/augsburg/de/page?id=1",
        "/augsburg/de/wp-json/extensions/v3/page?id=1",
        "integreat_cms/api/tests/expected-outputs/augsburg_de_page_1.json",
    ),
]


class ApiTest(TestCase):
    """
    This test class checks all endpoints defined in `endpoint_data`.
    It verifies that the content delivered by the endpoint is equivalent with the data
    provided in the corresponding json file.
    """

    fixtures = [
        "integreat_cms/cms/fixtures/test_data.json",
    ]

    @classmethod
    def setUpClass(cls):
        with disable_listeners():
            super().setUpClass()

    generate_test_functions(
        class_variables=vars(),
        endpoint_data=endpoint_data,
    )
