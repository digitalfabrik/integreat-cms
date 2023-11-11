from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import FieldDoesNotExist, PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import SingleObjectMixin

from ..constants import status

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.base import ModelBase
    from django.http import HttpRequest, HttpResponseRedirect
    from django.template.response import TemplateResponse
    from django.utils.functional import Promise

    from ..models import Language
    from ..models.abstract_content_model import AbstractContentModel, ContentQuerySet
    from ..models.abstract_content_translation import AbstractContentTranslation
    from ..models.events.event import EventQuerySet
    from ..models.pages.page import PageQuerySet

logger = logging.getLogger(__name__)


class ContentVersionView(PermissionRequiredMixin, SingleObjectMixin, TemplateView):
    """
    View for browsing the content versions and restoring old content versions
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name: str = "content_versions.html"

    #: The current language
    language: Language | None = None

    #: The current content model (see :class:`~django.views.generic.detail.SingleObjectMixin`)
    model: ModelBase | None = None

    #: The current content object (see :class:`~django.views.generic.detail.SingleObjectMixin`)
    object: AbstractContentModel | None = None

    #: All translations of the content object in the current language
    translations: list[AbstractContentTranslation] = []

    #: The currently selected translation version
    selected_version: AbstractContentTranslation | None = None

    #: The label of the "back to form" button
    back_to_form_label: Promise = _("Back to the form")

    @property
    def model_name(self) -> str:
        """
        The name of this model

        :returns: The name of this model
        """
        if TYPE_CHECKING:
            assert self.model
        return self.model._meta.model_name.lower()

    @property
    def pk_url_kwarg(self) -> str:
        """
        The name of the URLConf keyword argument that contains the primary key.
        By default, pk_url_kwarg is 'pk'.
        See :attr:`django:django.views.generic.detail.SingleObjectMixin.pk_url_kwarg`.

        :returns: The name of URL kwarg of the id
        """
        return f"{self.model_name}_id"

    @property
    def edit_url(self) -> str:
        """
        The url to the form in the current language

        :returns: The edit url
        """
        if TYPE_CHECKING:
            assert self.request.region
            assert self.language
            assert self.object
        return reverse(
            f"edit_{self.model_name}",
            kwargs={
                "region_slug": self.request.region.slug,
                "language_slug": self.language.slug,
                self.pk_url_kwarg: self.object.id,
            },
        )

    @property
    def versions_url(self) -> str:
        """
        The url to the form in the current language

        :returns: The edit url
        """
        if TYPE_CHECKING:
            assert self.request.region
            assert self.language
            assert self.object
        return reverse(
            f"{self.model_name}_versions",
            kwargs={
                "region_slug": self.request.region.slug,
                "language_slug": self.language.slug,
                self.pk_url_kwarg: self.object.id,
            },
        )

    def has_view_permission(self) -> bool:
        """
        Whether the user has the permission to change objects

        :returns: Whether the user can change objects
        """
        return self.request.user.has_perm(f"cms.view_{self.model_name}")

    def has_change_permission(self) -> bool:
        """
        Whether the user has the permission to change objects

        :returns: Whether the user can change objects
        """
        return self.request.user.has_perm(f"cms.change_{self.model_name}")

    def has_publish_permission(self) -> bool:
        """
        Whether the user has the permission to publish objects

        :returns: Whether the user can publish objects
        """
        return self.request.user.has_perm(f"cms.publish_{self.model_name}")

    def has_permission(self) -> bool:
        """
        Override :meth:`django:django.contrib.auth.mixins.PermissionRequiredMixin.has_permission`

        :returns: Whether the current user can access this view
        """
        archived = getattr(self.object, "archived", False)
        if self.request.method == "POST":
            # Archived objects cannot be changed
            if archived:
                return False
            if self.request.POST.get("status") == status.PUBLIC:
                return self.has_publish_permission()
            return self.has_change_permission()
        if archived:
            messages.warning(
                self.request,
                _("You cannot restore versions of this page because it is archived."),
            )
        return self.has_view_permission()

    def get_queryset(self) -> ContentQuerySet | (EventQuerySet | PageQuerySet):
        """
        Filter the content objects by the current region

        :raises ~django.http.Http404: HTTP status 404 if the content is not found

        :return: The rendered template response
        """
        return super().get_queryset().filter(region=self.request.region)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Get revision context data

        :return: The context dictionary
        """
        if TYPE_CHECKING:
            assert self.selected_version
            assert self.model
        context = super().get_context_data(**kwargs)

        api_version = next(
            (t for t in self.translations if t.status == status.PUBLIC), None
        )

        try:
            slug_label = self.selected_version._meta.get_field("slug").verbose_name
        except FieldDoesNotExist:
            slug_label = _("Link to the {}").format(self.model._meta.verbose_name)

        context.update(
            {
                "language": self.language,
                "translations": self.translations,
                "selected_version": self.selected_version,
                "api_version": api_version,
                "edit_url": self.edit_url,
                "versions_url": self.versions_url,
                "back_to_form_label": self.back_to_form_label,
                "slug_label": slug_label,
                "title_label": self.selected_version._meta.get_field(
                    "title"
                ).verbose_name,
                "content_label": self.selected_version._meta.get_field(
                    "content"
                ).verbose_name,
                "can_edit": self.has_change_permission(),
                "can_publish": self.has_publish_permission(),
            }
        )

        return context

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect | TemplateResponse:
        r"""
        Validate the versions view

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

        :return: The rendered template response
        """
        self.object = self.get_object()
        if TYPE_CHECKING:
            assert self.object

        self.language = self.request.region.get_language_or_404(
            kwargs.get("language_slug"), only_active=True
        )

        self.translations = self.object.translations.filter(language=self.language)

        if not self.translations:
            return redirect(self.edit_url)

        if selected_version_number := kwargs.get("selected_version"):
            try:
                self.selected_version = next(
                    translation
                    for translation in self.translations
                    if translation.version == int(selected_version_number)
                )
            except StopIteration:
                messages.error(
                    self.request,
                    _("The version {} does not exist.").format(selected_version_number),
                )
                return redirect(self.versions_url)
        else:
            self.selected_version = self.translations[0]

        return super().dispatch(request, *args, **kwargs)

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        r"""
        Restore a previous revision of a page translation

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

        :return: The rendered template response
        """

        if desired_status := request.POST.get("status"):
            try:
                restored_version_number = int(request.POST.get("revision"))
                restored_version = next(
                    translation
                    for translation in self.translations
                    if translation.version == restored_version_number
                )
                restored_version.status = desired_status
            except StopIteration:
                messages.error(
                    self.request,
                    _("The version {} does not exist.").format(restored_version_number),
                )
                return redirect(self.versions_url)
            if desired_status not in dict(status.CHOICES):
                raise PermissionDenied(
                    f"{request.user!r} tried to restore {restored_version!r} of {self.object!r} with invalid status {desired_status!r}"
                )
        else:
            # If the current version should be rejected, return to the latest version that is neither an auto save nor in review
            try:
                restored_version = next(
                    translation
                    for translation in self.translations
                    if translation.status in [status.DRAFT, status.PUBLIC]
                )
                desired_status = restored_version.status
            except StopIteration:
                messages.error(
                    request,
                    _("You cannot reject changes if there is no version to return to."),
                )
                return redirect(self.versions_url)

        current_version = self.translations[0]

        # Assume that changing to an older version is not a minor change by default
        restored_version.minor_edit = False
        if (
            restored_version.slug == current_version.slug
            and restored_version.title == current_version.title
            and restored_version.content == current_version.content
        ):
            restored_version.minor_edit = True
            if desired_status == status.PUBLIC:
                if current_version.status == status.PUBLIC:
                    messages.info(request, _("No changes detected, but date refreshed"))
                else:
                    messages.success(
                        request,
                        _("No changes detected, but status changed to published"),
                    )
            else:
                messages.error(
                    request,
                    _(
                        "This version is identical to the current version of this translation."
                    ),
                )
                return redirect(self.versions_url)
        else:
            messages.success(request, _("The version was successfully restored"))

        self.restore_version(restored_version)

        return redirect(self.versions_url)

    def restore_version(self, restored_version: Any) -> None:
        """
        Restore the given version

        :param restored_version: The version which should be restored
        """
        current_version = self.translations[0]
        # Delete all now outdated links
        current_version.links.all().delete()
        # Create new version
        restored_version.pk = None
        restored_version.version = current_version.version + 1
        # Reset author to current user
        restored_version.creator = self.request.user
        restored_version.save()
