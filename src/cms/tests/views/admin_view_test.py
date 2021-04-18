from django.contrib.auth import get_user_model

from ...models import UserProfile
from .view_test import ViewTest
from .view_test_utils import generate_test_functions


admin_views = [
    "admin_dashboard",
    "admin_settings",
    "languages",
    "new_language",
    "new_offer_template",
    "new_organization",
    "new_region",
    "new_role",
    "new_user",
    "offer_templates",
    "organizations",
    "regions",
    "regions",
    "regions",
    "regions",
    "roles",
    "user_settings",
    "authenticate_modify_mfa",
    "users",
]


class AdminViewTest(ViewTest):
    """
    This test checks whether all admin views return status code 200.
    """

    def setUp(self):
        user = get_user_model().objects.create_superuser(
            username="root", password="", email=""
        )
        UserProfile.objects.create(user=user)
        self.client.force_login(user)

    generate_test_functions(class_variables=vars(), views=admin_views, kwargs={})
