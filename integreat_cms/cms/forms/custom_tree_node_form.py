from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from treebeard.forms import MoveNodeForm

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.base import ModelBase

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
        self.fields["_ref_node_id"].widget = forms.HiddenInput()
        self.fields["_position"].widget = forms.HiddenInput()

    def _clean_cleaned_data(self) -> tuple[str, int]:
        """
        Delete auxiliary fields not belonging to node model and include instance attributes in cleaned_data

        :return: The initial data for _ref_node_id and _position fields
        """
        # This workaround is required because the MoveNodeForm does not take
        # instance attribute into account which are not included in cleaned_data
        self.cleaned_data["region"] = self.instance.region
        return super()._clean_cleaned_data()

    def _get_position_ref_node(
        self, instance: LanguageTreeNode | Page
    ) -> dict[str, str]:
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
                    "Node %r is now referenced left to node %r", instance, next_sibling
                )
                return {"_ref_node_id": str(next_sibling.id), "_position": "left"}
            # If the page is the only root page of this region, do not reference other nodes
            logger.debug(
                "Node %r is the only root node of its region and now referenced to no other node",
                instance,
            )
            return {"_ref_node_id": "", "_position": "first-child"}
        # Convert initial data to string to fix the change detection
        initial_data = super()._get_position_ref_node(instance)
        return {key: str(value) for key, value in initial_data.items()}

    @classmethod
    def mk_dropdown_tree(
        cls, model: ModelBase, for_node: None | (LanguageTreeNode | Page) = None
    ) -> list:
        """
        Creates a tree-like list of choices. Overwrites the parent method because the field is hidden anyway and
        additional queries to render the node titles should be avoided.

        :param model: ~integreat_cms.cms.models.abstract_tree_node.AbstractTreeNode
        :param for_node: The instance of this form
        :return: A list of select options
        """
        # No need to calculate anything here, because we set self.fields["_ref_node_id"].choices manually
        return []
