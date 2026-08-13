from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from treebeard.forms import MoveNodeForm

if TYPE_CHECKING:
    from typing import Any

    from django.forms.models import ModelFormOptions

    from ..models import LanguageTreeNode, Page

logger = logging.getLogger(__name__)


class CustomTreeNodeForm(MoveNodeForm):
    """
    Form for creating and modifying tree node objects
    """

    def __init__(self, **kwargs: Any) -> None:
        r"""
        Initialize custom tree node form

        :param \**kwargs: The supplied keyword arguments
        """

        # Instantiate MoveNodeForm
        super().__init__(**kwargs)

        # Hide tree node inputs
        self.fields["treebeard_ref_node"].widget = forms.HiddenInput()
        self.fields["treebeard_position"].widget = forms.HiddenInput()

    def _get_initial(
        self,
        instance: LanguageTreeNode | Page,
    ) -> dict[str, Any]:
        """
        Get the initial values for the referenced node and the position

        :param instance: The node instance
        :return: A dictionary containing the initial values
        """
        prev_sibling = instance.get_prev_sibling()
        # If the previous sibling is of another region, use a different node as reference
        if prev_sibling and prev_sibling.region != instance.region:
            logger.debug(
                "Node %r was referenced to node %r of another region",
                instance,
                prev_sibling,
            )
            next_sibling = instance.get_next_sibling()
            # If the next sibling exists and is of this region, reference this instance to the left of the next sibling
            if next_sibling and next_sibling.region == instance.region:
                logger.debug(
                    "Node %r is now referenced left to node %r",
                    instance,
                    next_sibling,
                )
                return {
                    "treebeard_ref_node": next_sibling,
                    "treebeard_position": "left",
                }
            # If the page is the only root page of this region, do not reference other nodes
            logger.debug(
                "Node %r is the only root node of its region and now referenced to no other node",
                instance,
            )
            return {"treebeard_ref_node": None, "treebeard_position": "first-child"}
        return super()._get_initial(instance)

    def _set_ref_model_queryset(
        self,
        opts: ModelFormOptions,
        instance: LanguageTreeNode | Page | None,  # noqa: ARG002
    ) -> None:
        """
        Set the queryset of the (hidden) reference node field. Overwrites the parent
        method because it queries the whole cross-region tree; the subclasses limit
        the queryset to the nodes of the current region instead.

        :param opts: The model form options
        :param instance: The instance of this form
        """
        self.fields["treebeard_ref_node"].queryset = opts.model.objects.all()

    def save(self, commit: bool = True) -> Any:
        """
        Save the form instance. Since django-treebeard 5, ``MoveNodeForm.save()`` skips
        its tree logic if the treebeard fields are unchanged - but our forms pre-populate
        them via field initials, so new nodes must still be created at the requested position.

        :param commit: Whether or not the changes should be written to the database
        :return: The saved node instance
        """
        if self.instance._state.adding:
            for name in ("treebeard_ref_node", "treebeard_position"):
                if name not in self.changed_data:
                    self.changed_data.append(name)
        return super().save(commit=commit)
