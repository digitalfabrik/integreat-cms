"""
This module contains mixins for our views
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin, TemplateResponseMixin

from ...core.utils.machine_translation_provider import MachineTranslationProvider

if TYPE_CHECKING:
    from typing import Any


class RegionPermissionRequiredMixing(UserPassesTestMixin):
    """
    A mixin that can be used for class-based views that require that the user is has access to the current region of this request
    """

    def test_func(self) -> bool:
        """
        The test this account has to pass

        :return: Whether this account has passed the test
        """
        # Superusers and staff have permissions for all regions
        return (
            self.request.user.is_superuser
            or self.request.user.is_staff
            or self.request.region in self.request.user.regions.all()
        )


class ModelTemplateResponseMixin(TemplateResponseMixin):
    """
    A mixin that can be used to render a template of a model (e.g. list or form)
    """

    @property
    def template_name(self) -> str:
        """
        Return the template name to be used for the request.

        :return: The template to be rendered
        """
        model_name = self.model._meta.model_name
        model_name_plural = self.model.get_model_name_plural()
        return f"{model_name_plural}/{model_name}{self.template_name_suffix}.html"


# pylint: disable=too-few-public-methods
class ModelConfirmationContextMixin(ContextMixin):
    """
    A mixin that can be used to inject confirmation text into a template of a model (e.g. list or form)
    """

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :return: The template context
        """
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this {}"
                ).format(self.model._meta.verbose_name),
                "delete_dialog_text": _("This cannot be reversed."),
            }
        )
        return context


class ContentEditLockMixin(ContextMixin):
    """
    A mixin that provides some variables required for the content edit lock
    """

    #: The reverse name of the url of the associated list view
    back_url_name: str | None = None

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :return: The template context
        """
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "back_url": reverse(
                    self.back_url_name,
                    kwargs={
                        "region_slug": kwargs["region_slug"],
                        "language_slug": kwargs["language_slug"],
                    },
                )
            }
        )
        return context


# pylint: disable=too-few-public-methods
class MachineTranslationContextMixin(ContextMixin):
    """
    This mixin provides extra context for machine translation options
    """

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :return: The template context
        """
        context = super().get_context_data(**kwargs)
        language_slug = kwargs["language_slug"]
        language_node = self.request.region.language_node_by_slug[language_slug]
        context["MT_PROVIDER"] = language_node.mt_provider
        context["MT_PERMITTED"] = (
            MachineTranslationProvider.is_permitted(
                self.request.region, self.request.user, self.translation_model
            )
            and not language_node.is_root()
            and not (
                language_node.mt_provider
                and language_node.mt_provider.bulk_only_for_staff
                and not self.request.user.is_staff
            )
        )
        return context
