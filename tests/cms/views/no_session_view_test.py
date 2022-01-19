from .view_test import ViewTest
from .view_test_utils import generate_test_functions


admin_views = [
    "login",
    "login_mfa",
    "login_mfa_assert",
    "password_reset",
]


class NoSessionViewTest(ViewTest):
    """
    This test checks whether all no-session views return status code 200.
    """

    generate_test_functions(class_variables=vars(), views=admin_views, kwargs={})
