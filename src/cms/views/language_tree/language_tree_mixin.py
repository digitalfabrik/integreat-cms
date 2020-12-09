from django.utils.translation import ugettext_lazy
from django.views.generic.base import ContextMixin

# pylint: disable=too-few-public-methods
class LanguageTreeMixin(ContextMixin):
    extra_context = {
        "delete_dialog_title": ugettext_lazy(
            "Please confirm that you really want to delete this language node"
        ),
        "delete_dialog_text": ugettext_lazy(
            "All translations for pages, locations, events and push notifications of this language will also be deleted."
        ),
    }
