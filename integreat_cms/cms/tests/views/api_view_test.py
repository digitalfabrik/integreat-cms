from linkcheck.listeners import disable_listeners

from .view_test import ViewTest
from .view_test_utils import generate_test_functions


views = [
    "api_regions",
    "api_regions_live",
    "api_regions_hidden",
]

region_views = [
    "api_languages",
]

region_language_views = [
    "api_pages",
    "api_pdf_export",
    "api_sent_push_notifications",
]


class APIViewTest(ViewTest):
    """
    This test checks whether all api views return status code 200.
    """

    fixtures = [
        "integreat_cms/cms/fixtures/roles.json",
        "integreat_cms/cms/fixtures/test_data.json",
    ]

    @classmethod
    def setUpClass(cls):
        with disable_listeners():
            super().setUpClass()

    generate_test_functions(
        class_variables=vars(),
        views=views,
        kwargs={},
    )

    generate_test_functions(
        class_variables=vars(),
        views=region_views,
        kwargs={"region_slug": "augsburg"},
    )

    generate_test_functions(
        class_variables=vars(),
        views=region_language_views,
        kwargs={"region_slug": "augsburg", "language_slug": "de"},
    )
