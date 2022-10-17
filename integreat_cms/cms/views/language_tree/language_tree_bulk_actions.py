import logging

from django.utils.translation import gettext_lazy as _

from cacheops import invalidate_obj

from ...models import LanguageTreeNode
from ..bulk_action_views import BulkUpdateBooleanFieldView

logger = logging.getLogger(__name__)


# pylint: disable=too-many-ancestors
class LanguageTreeBulkActionView(BulkUpdateBooleanFieldView):
    """
    Bulk action view for language tree nodes which flushes
    the cache for all content models after each operation
    """

    #: The model of this :class:`~integreat_cms.cms.views.bulk_action_views.BulkActionView`
    model = LanguageTreeNode

    @property
    def field_name(self):
        """
        Called when the bulk action is performed and the ``field_name`` attribute was not overwritten

        :raises NotImplementedError: If the ``field_name`` attribute is not implemented in the subclass
        """
        raise NotImplementedError(
            "Subclasses of LanguageTreeBulkActionView must provide a 'field_name' attribute"
        )

    @property
    def action(self):
        """
        Called when the bulk action is performed and the ``action`` attribute was not overwritten

        :raises NotImplementedError: If the ``action`` attribute is not implemented in the subclass
        """
        raise NotImplementedError(
            "Subclasses of LanguageTreeBulkActionView must provide an 'action' attribute"
        )

    def post(self, request, *args, **kwargs):
        r"""
        Execute bulk action for language tree node and flush the cache

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The redirect
        :rtype: ~django.http.HttpResponseRedirect
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


# pylint: disable=too-many-ancestors
class BulkMakeVisibleView(LanguageTreeBulkActionView):
    """
    Bulk action for making multiple language tree nodes visible at once
    """

    #: The name of the archived-field
    field_name = "visible"

    #: The name of the action
    action = _("made visible")


# pylint: disable=too-many-ancestors
class BulkHideView(BulkMakeVisibleView):
    """
    Bulk action for hiding multiple language tree nodes at once
    """

    #: The value of the field
    value = False

    #: The name of the action
    action = _("hidden")


# pylint: disable=too-many-ancestors
class BulkActivateView(LanguageTreeBulkActionView):
    """
    Bulk action for activating multiple language tree nodes at once
    """

    #: The name of the archived-field
    field_name = "active"

    #: The name of the action
    action = _("activated")


# pylint: disable=too-many-ancestors
class BulkDisableView(BulkActivateView):
    """
    Bulk action for disabling multiple language tree nodes at once
    """

    #: The value of the field
    value = False

    #: The name of the action
    action = _("disabled")
