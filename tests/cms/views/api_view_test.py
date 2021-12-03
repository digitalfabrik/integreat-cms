from linkcheck.listeners import disable_listeners

from .view_test import ViewTest
from .view_test_utils import generate_test_functions


views = [
    "api:regions",
    "api:regions_live",
    "api:regions_hidden",
]

region_views = [
    "api:languages",
]

region_language_views = [
    "api:pages",
    "api:pdf_export",
    "api:sent_push_notifications",
]


class APIViewTest(ViewTest):
    """
    This test checks whether all api views return status code 200.
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
