from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from treebeard.ns_tree import NS_NodeQuerySet

from ...models import LanguageTreeNode, PageTranslation
from ..machine_translation_form import MachineTranslationForm

logger = logging.getLogger(__name__)


class PageTranslationForm(MachineTranslationForm):
    """
    Form for creating and modifying page translation objects
    """

    def user_has_publish_rights(self) -> bool:
        """
        Helper method to check if the current user has permission to publish the page
        """
        if page_obj := self.instance.page:
            return self.request.user.has_perm("cms.publish_page_object", page_obj)
        return self.request.user.has_perm("cms.publish_page")

    def mt_form_is_enabled(self) -> NS_NodeQuerySet:
        """
        For pages, machine translations should only be enabled if the user has publishing rights
        """
        if not self.user_has_publish_rights():
            return LanguageTreeNode.objects.none()
        return super().mt_form_is_enabled()

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = PageTranslation
        #: The fields of the model which should be handled by this form
        fields = [
            *MachineTranslationForm.Meta.fields,
            "slug",
            "hix_score",
            "hix_feedback",
        ]
