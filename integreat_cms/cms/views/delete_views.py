"""
This module contains deletion views for our models that don't need custom handling.
"""
import logging
from django.contrib import messages
from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
)
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import DeleteView

logger = logging.getLogger(__name__)


# pylint: disable=too-many-ancestors
class CustomModelDeleteMixin(
    PermissionRequiredMixin,
):
    """
    This mixin handles error messages in form views of subclasses of
    :class:`~integreat_cms.cms.forms.custom_model_form.CustomModelForm`
    """

    #: Whether the objects should be protected from deletion if it is used in many to many relationships
    protect_manytomany = None

    def get_permission_required(self):
        """
        Override this method to override the permission_required attribute.

        :return: The permissions that are required for views inheriting from this Mixin
        :rtype: ~collections.abc.Iterable
        """
        return (f"cms.delete_{self.model._meta.model_name}",)

    def get_success_url(self):
        """
        Determine the URL to redirect to when the object is successfully deleted

        :return: The url to redirect on success
        :rtype: str
        """
        return reverse(f"{self.object._meta.model_name}s")

    def delete(self, request, *args, **kwargs):
        r"""
        Call the delete() method on the fetched object and then redirect to the
        success URL.

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises django.db.IntegrityError: If the object has many to many relationships that prevent deletion

        :return: A redirection to the ``success_url``
        :rtype: ~django.http.HttpResponseRedirect
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
    http_method_names = ["post"]
