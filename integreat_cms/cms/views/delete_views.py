"""
This module contains deletion views for our models that don't need custom handling.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class CustomModelDeleteMixin(
    PermissionRequiredMixin,
):
    """
    This mixin handles error messages in form views of subclasses of
    :class:`~integreat_cms.cms.forms.custom_model_form.CustomModelForm`
    """

    #: Whether the objects should be protected from deletion if it is used in many to many relationships
    protect_manytomany: str | None = None

    def get_permission_required(self) -> tuple[str, ...]:
        """
        Override this method to override the permission_required attribute.

        :return: The permissions that are required for views inheriting from this Mixin
        """
        return (f"cms.delete_{self.model._meta.model_name}",)

    def get_success_url(self) -> str:
        """
        Determine the URL to redirect to when the object is successfully deleted

        :return: The url to redirect on success
        """
        kwargs = {}
        if self.request.region:
            kwargs["region_slug"] = self.request.region.slug
        return reverse(self.object.get_model_name_plural(), kwargs=kwargs)

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Call the delete() method on the fetched object and then redirect to the
        success URL.

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises django.db.IntegrityError: If the object has many to many relationships that prevent deletion

        :return: A redirection to the ``success_url``
        """
        self.object = self.get_object()
        # Check whether object has many to many relationships that should prevent deleting
        if self.protect_manytomany:
            manytomany_manager = getattr(self.object, self.protect_manytomany)
            if manytomany_manager.exists():
                raise IntegrityError(
                    f"The object {self.object!r} cannot be deleted because of the following many to many relationship: {manytomany_manager.all()}"
                )
        success_url = self.get_success_url()
        self.object.delete()
        logger.info("%r deleted by %r", self.object, request.user)
        messages.success(
            request,
            _('{} "{}" was successfully deleted').format(
                self.object._meta.verbose_name, self.object
            ),
        )
        return HttpResponseRedirect(success_url)


class CustomDeleteView(CustomModelDeleteMixin, DeleteView):
    """
    View for deleting an object retrieved with self.get_object()
    """

    #: The list of HTTP method names that this view will accept.
    #: Since we're doing confirmation dynamically, we don't need the get-request part of this view
    http_method_names: list[str] = ["post"]
