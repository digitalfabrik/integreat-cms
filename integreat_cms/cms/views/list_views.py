"""
This module contains list views for our models that don't need custom handling.
"""
import logging
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.conf import settings
from django.views.generic.list import ListView

from .mixins import (
    ModelTemplateResponseMixin,
    ModelConfirmationContextMixin,
)

logger = logging.getLogger(__name__)


# pylint: disable=too-many-ancestors
class ModelListView(
    PermissionRequiredMixin,
    ModelTemplateResponseMixin,
    ModelConfirmationContextMixin,
    ListView,
):
    """
    Render some list of objects, set by ``self.model`` or ``self.queryset``.
    """

    #: The internal attribute of the model property
    _model = None

    @property
    def paginate_by(self):
        """
        An integer specifying how many objects should be displayed per page.
        This either returns the current ``size`` GET parameter or the value defined in
        :attr:`~integreat_cms.core.settings.PER_PAGE`.
        (see :class:`~django.views.generic.list.MultipleObjectMixin`)

        :return: The page size
        :rtype: int
        """
        return self.request.GET.get("size", settings.PER_PAGE)

    @property
    def model(self):
        """
        Return the model class of this list view.

        :return: The corresponding Django model
        :rtype: ~django.db.models.Model
        """
        return self._model or self.queryset.model

    @model.setter
    def model(self, value):
        self._model = value

    @property
    def context_object_name(self):
        """
        Designates the name of the variable to use in the context
        (see :class:`~django.views.generic.list.MultipleObjectMixin`).

        :return: The name of the objects in this list view
        :rtype: str
        """
        return self.model.get_model_name_plural()

    def get_context_data(self, **kwargs):
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :type \**kwargs: dict

        :return: The template context
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        context["current_menu_item"] = self.model.get_model_name_plural()
        return context

    def get_permission_required(self):
        """
        Override this method to override the permission_required attribute.

        :return: The permissions that are required for views inheriting from this Mixin
        :rtype: ~collections.abc.Iterable
        """
        return (f"cms.view_{self.model._meta.model_name}",)

    def get_queryset(self):
        """
        Get the model's queryset (optionally filtered by the current region)

        :return: The queryset of the current list view
        :rtype: ~django.db.models.query.QuerySet
        """
        queryset = super().get_queryset()
        if self.request.region:
            # Only return objects of the current region
            queryset = queryset.filter(region=self.request.region)
        return queryset
