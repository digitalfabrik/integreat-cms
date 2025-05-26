"""
.. warning::
    Any action modifying the database with treebeard should use ``@tree_mutex(MODEL_NAME)`` from ``integreat_cms.cms.utils.tree_mutex``
    as a decorator instead of ``@transaction.atomic`` to force treebeard to actually use transactions.
    Otherwise, the data WILL get corrupted during concurrent treebeard calls!
"""

from __future__ import annotations

import logging
from typing import cast, TYPE_CHECKING

from cacheops import invalidate_obj
from django.contrib import messages
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext, ngettext_lazy

from ...models import (
    EventTranslation,
    LanguageTreeNode,
    PageTranslation,
    POITranslation,
)
from ...utils.stringify_list import iter_to_string
from ...utils.tree_mutex import tree_mutex
from ..bulk_action_views import BulkUpdateBooleanFieldView

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponseRedirect

logger = logging.getLogger(__name__)


class LanguageTreeBulkActionView(BulkUpdateBooleanFieldView):
    """
    Bulk action view for language tree nodes which flushes
    the cache for all content models after each operation
    """

    #: The model of this :class:`~integreat_cms.cms.views.bulk_action_views.BulkActionView`
    model = LanguageTreeNode

    @property
    def field_name(self) -> str:
        """
        Called when the bulk action is performed and the ``field_name`` attribute was not overwritten

        :raises NotImplementedError: If the ``field_name`` attribute is not implemented in the subclass
        """
        raise NotImplementedError(
            "Subclasses of LanguageTreeBulkActionView must provide a 'field_name' attribute",
        )

    @property
    def action(self) -> str:
        """
        Called when the bulk action is performed and the ``action`` attribute was not overwritten

        :raises NotImplementedError: If the ``action`` attribute is not implemented in the subclass
        """
        raise NotImplementedError(
            "Subclasses of LanguageTreeBulkActionView must provide an 'action' attribute",
        )

    @tree_mutex("languagetreenode")
    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseRedirect:
        r"""
        Execute bulk action for language tree node and flush the cache

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        # Execute bulk action
        response = super().post(request, *args, **kwargs)

        # Flush cache of content objects
        for page in self.request.region.pages.all():
            invalidate_obj(page)
        for poi in self.request.region.pois.all():
            invalidate_obj(poi)
        for event in self.request.region.events.all():
            invalidate_obj(event)

        # Let the base view handle the redirect
        return response


class BulkMakeVisibleView(LanguageTreeBulkActionView):
    """
    Bulk action for making multiple language tree nodes visible at once
    """

    #: The name of the archived-field
    field_name = "visible"

    #: The name of the action
    action = _("made visible")


class BulkHideView(BulkMakeVisibleView):
    """
    Bulk action for hiding multiple language tree nodes at once
    """

    #: The value of the field
    value = False

    #: The name of the action
    action = _("hidden")


class BulkActivateView(LanguageTreeBulkActionView):
    """
    Bulk action for activating multiple language tree nodes at once
    """

    #: The name of the archived-field
    field_name = "active"

    #: The name of the action
    action = _("activated")

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseRedirect:
        for language_tree_node in self.get_queryset():
            models = [PageTranslation, EventTranslation, POITranslation]
            for model in models:
                filters = {
                    f"{model.foreign_field()}__region": request.region,
                    "language": language_tree_node.language,
                }
                distinct = [f"{model.foreign_field()}__pk", "language__pk"]
                for translation in model.objects.filter(**filters).distinct(*distinct):
                    if self.value:
                        translation.save(update_timestamp=False)
                    else:
                        translation.links.all().delete()

        # Execute bulk action
        return super().post(request, *args, **kwargs)


class BulkDisableView(BulkActivateView):
    """
    Bulk action for disabling multiple language tree nodes at once
    """

    #: The value of the field
    value = False

    #: The name of the action
    action = _("disabled")

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseRedirect:
        compliant_ltn = []
        non_compliant_ltn = []
        for language_tree_node in self.get_queryset():
            if language_tree_node.visible:
                non_compliant_ltn.append(language_tree_node)
            else:
                compliant_ltn.append(language_tree_node)
        self._use_subset = True
        response = super().post(request, *args, **kwargs)
        self._use_subset = False
        list(messages.get_messages(request))
        if compliant_ltn:
            messages.success(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} was successfully deactivated.",
                    "The following {model_name} were successfully deactivated: {object_names}",
                    len(compliant_ltn),
                ).format(
                    model_name=ngettext(
                        self.model._meta.verbose_name.title(),
                        self.model._meta.verbose_name_plural,
                        len(compliant_ltn),
                    ),
                    object_names=iter_to_string(compliant_ltn),
                ),
            )
        if non_compliant_ltn:
            messages.error(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} could not be deactivated, because inactive language tree nodes cannot be visible.",
                    "The following {model_name} could not be deactivated, because inactive language tree nodes cannot be visible: {object_names}",
                    len(compliant_ltn),
                ).format(
                    model_name=ngettext(
                        self.model._meta.verbose_name.title(),
                        self.model._meta.verbose_name_plural,
                        len(non_compliant_ltn),
                    ),
                    object_names=iter_to_string(non_compliant_ltn),
                ),
            )
        return response

    def get_queryset(self) -> Any:
        """
        Get the queryset of selected items for this bulk action

        :raises ~django.http.Http404: HTTP status 404 if no objects with the given ids exist

        :return: The QuerySet of the filtered links
        """

        queryset = cast(QuerySet[LanguageTreeNode], super().get_queryset())

        # Filter for subset that complies with constraint
        if getattr(self, "_use_subset", False):
            queryset = queryset.filter(visible=False)

        return queryset
