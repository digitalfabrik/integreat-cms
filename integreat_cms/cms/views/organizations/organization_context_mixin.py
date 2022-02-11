from django.views.generic.base import ContextMixin
from django.utils.translation import ugettext_lazy


# pylint: disable=too-few-public-methods
class OrganizationContextMixin(ContextMixin):
    """
    This mixin provides extra context for organization views
    """

    extra_context = {
        "delete_dialog_title": ugettext_lazy(
            "Please confirm that you really want to delete this organization"
        ),
        "delete_dialog_text": ugettext_lazy(
            "This will update all pages and users that are part of this organization."
        ),
    }
