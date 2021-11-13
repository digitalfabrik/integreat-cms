import logging

from django.utils.translation import ugettext_lazy
from django.views.generic.base import ContextMixin

logger = logging.getLogger(__name__)

# pylint: disable=too-few-public-methods
class LanguageTreeContextMixin(ContextMixin):
    """
    This mixin provides extra context for language tree views
    """

    #: A dictionary of additional context
    extra_context = {
        "delete_dialog_title": ugettext_lazy(
            "Please confirm that you really want to delete this language node"
        ),
        "delete_dialog_text": ugettext_lazy(
            "All translations for pages, locations, events and push notifications of this language will also be deleted."
        ),
    }
