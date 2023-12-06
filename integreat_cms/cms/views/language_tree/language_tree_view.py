from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db import ModelBase

from ...models import LanguageTreeNode
from ..list_views import ModelListView
from .language_tree_context_mixin import LanguageTreeContextMixin

logger = logging.getLogger(__name__)


# pylint: disable=too-many-ancestors
class LanguageTreeView(LanguageTreeContextMixin, ModelListView):
    """
    View for rendering the language tree view.
    This view is available in regions.
    """

    #: The model of this list view
    model: ModelBase = LanguageTreeNode
    #: Disable pagination for language tree
    paginate_by: int | None = None

    def get_queryset(self) -> list[LanguageTreeNode]:
        """
        Get language tree queryset

        :return: The language tree of the current region
        """
        # Return the annotated language tree of the current region to save a few database queries
        return self.request.region.language_tree
