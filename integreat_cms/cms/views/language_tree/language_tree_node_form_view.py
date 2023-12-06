from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.urls import reverse

from ...forms import LanguageTreeNodeForm
from ...models import EventTranslation, PageTranslation, POITranslation
from ..form_views import CustomCreateView, CustomUpdateView

if TYPE_CHECKING:
    from typing import Any

    from django.http.response import HttpResponseRedirect

logger = logging.getLogger(__name__)


class LanguageTreeNodeCreateView(CustomCreateView):
    """
    Class that handles creating language tree nodes.
    This view is available within regions.
    """

    #: The form class of this form view
    form_class = LanguageTreeNodeForm

    def get_success_url(self) -> str:
        """
        Determine the URL to redirect to when the form is successfully validated

        :return: The url to redirect on success
        """
        if "submit_add_new" in self.request.POST:
            # If the "Create and add more" button was clicked, redirect to the new creation form
            return reverse(
                "new_languagetreenode",
                kwargs={"region_slug": self.request.region.slug},
            )
        return super().get_success_url()

    def get_form_kwargs(self) -> dict[str, Any]:
        """
        Return the keyword arguments for instantiating the form

        :return: The form kwargs
        """
        kwargs = super().get_form_kwargs()
        kwargs["region"] = self.request.region
        return kwargs


class LanguageTreeNodeUpdateView(CustomUpdateView):
    """
    Class that handles activating/deactivating of a language tree node
    """

    def form_valid(self, form: LanguageTreeNodeForm) -> HttpResponseRedirect:
        response = super().form_valid(form)

        language_tree_node = self.get_object()

        if "active" in form.changed_data:
            models = [PageTranslation, EventTranslation, POITranslation]
            for model in models:
                filters = {
                    f"{model.foreign_field()}__region": language_tree_node.region,
                    "language": language_tree_node.language,
                }
                distinct = [f"{model.foreign_field()}__pk", "language__pk"]
                for translation in model.objects.filter(**filters).distinct(*distinct):
                    if language_tree_node.active:
                        translation.save(update_timestamp=False)
                    else:
                        translation.links.all().delete()
        return response
