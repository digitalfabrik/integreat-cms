"""
This module contains the base view for bulk actions
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cacheops import invalidate_model
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from django.views.generic import RedirectView
from django.views.generic.list import MultipleObjectMixin

from ..constants import status
from ..models import Page, POI
from ..utils.stringify_list import iter_to_string
from .utils.publication_status import change_publication_status

if TYPE_CHECKING:
    from typing import Any

    from django.forms import ModelForm
    from django.http import HttpRequest, HttpResponse
    from django.http.response import HttpResponseRedirect

logger = logging.getLogger(__name__)


class BulkActionView(PermissionRequiredMixin, MultipleObjectMixin, RedirectView):
    """
    View for executing a bulk action and redirect to a given location
    """

    #: The list of HTTP method names that this view will accept.
    #: The bulk action form uses only POST as submission method.
    http_method_names: list[str] = ["post"]
    #: Whether the view requires change permissions
    require_change_permission: bool = True
    #: Whether the translation objects should be prefetched
    prefetch_translations: bool = False
    #: Whether the public translation objects should be prefetched
    prefetch_public_translations: bool = False

    def get_permission_required(self) -> tuple[str]:
        """
        Override this method to override the permission_required attribute.

        :return: The permissions that are required for views inheriting from this Mixin
        """
        # If the bulk action performs changes to the database, require the change permission
        if self.require_change_permission:
            return (f"cms.change_{self.model._meta.model_name}",)
        # If the bulk action is just a read-view (e.g. export), require the view permission
        return (f"cms.view_{self.model._meta.model_name}",)

    def get_redirect_url(self, *args: Any, **kwargs: Any) -> str:
        r"""
        Retrieve url for redirection

        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: url to redirect to
        """
        redirect_kwargs = {
            "region_slug": self.request.region.slug,
        }
        # If this bulk action is bound to a language url parameter, also pass this to the redirect url
        if "language_slug" in kwargs:
            redirect_kwargs["language_slug"] = kwargs["language_slug"]
        return reverse(f"{self.model._meta.model_name}s", kwargs=redirect_kwargs)

    def get_queryset(self) -> Any:
        """
        Get the queryset of selected items for this bulk action

        :raises ~django.http.Http404: HTTP status 404 if no objects with the given ids exist

        :return: The QuerySet of the filtered links
        """
        # This workaround is necessary to enable the async tests for the SUMM.AI client
        logger.debug("request body: %s", self.request.body)
        queryset = (
            super()
            .get_queryset()
            .filter(
                region=self.request.region,
                id__in=self.request.POST.getlist("selected_ids[]"),
            )
        )
        if not queryset:
            raise Http404(f"No {self.model._meta.object_name} matches the given query.")
        if self.prefetch_translations:
            queryset = queryset.prefetch_translations()
        if self.prefetch_public_translations:
            queryset = queryset.prefetch_public_translations()
        return queryset


class BulkMachineTranslationView(BulkActionView):
    """
    Bulk action for automatically translating multiple objects
    """

    #: Whether the public translation objects should be prefetched
    prefetch_translations: bool = True

    #: the form of this bulk action
    form: ModelForm | None = None

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        r"""
        Translate multiple objects automatically

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        if TYPE_CHECKING:
            assert self.form
        language_slug = kwargs["language_slug"]
        language_node = request.region.language_node_by_slug.get(language_slug)
        if not language_node or not language_node.active:
            raise Http404("No language matches the given query.")
        if not language_node.mt_provider:
            messages.error(
                request,
                _('Machine translations are disabled for language "{}"').format(
                    language_node
                ),
            )
            return super().post(request, *args, **kwargs)
        if not language_node.mt_provider.is_permitted(
            request.region, request.user, self.form._meta.model
        ):
            messages.error(
                request,
                _(
                    "Machine translations are not allowed for the current user or content type"
                ).format(language_node),
            )
            return super().post(request, *args, **kwargs)
        if language_node.mt_provider.bulk_only_for_staff and not request.user.is_staff:
            raise PermissionDenied(
                f"Only staff users have the permission to bulk translate {self.form._meta.model._meta.model_name} via {language_node.mt_provider}"
            )

        to_translate = language_node.mt_provider.is_needed(
            request.region, self.get_queryset(), language_node
        )
        if not to_translate:
            messages.error(
                request,
                _("All the selected translations are already up-to-date."),
            )
            return super().post(request, *args, **kwargs)

        already_up_to_date_translations = [
            content_object.best_translation.title
            for content_object in self.get_queryset()
            if content_object not in to_translate
        ]
        if already_up_to_date_translations:
            messages.error(
                request,
                ngettext_lazy(
                    "There already is an up-to-date translation for {}",
                    "There already are up-to-date translations for {}",
                    len(already_up_to_date_translations),
                ).format(iter_to_string(already_up_to_date_translations)),
            )

        logger.debug(
            "Machine translation via %s into %r for: %r",
            language_node.mt_provider.name,
            language_node.language,
            to_translate,
        )
        api_client = language_node.mt_provider.api_client(request, self.form)
        api_client.translate_queryset(to_translate, language_node.slug)

        # Let the base view handle the redirect
        return super().post(request, *args, **kwargs)


class BulkUpdateBooleanFieldView(BulkActionView):
    """
    Bulk action for toggling boolean fields of multiple objects at once
    """

    #: The value of the field (defaults to ``True``)
    value: bool = True

    @property
    def field_name(self) -> str:
        """
        Called when the bulk action is performed and the ``field_name`` attribute was not overwritten

        :raises NotImplementedError: If the ``field_name`` attribute is not implemented in the subclass
        """
        raise NotImplementedError(
            "Subclasses of BulkUpdateBooleanFieldView must provide a 'field_name' attribute"
        )

    @property
    def action(self) -> str:
        """
        Called when the bulk action is performed and the ``action`` attribute was not overwritten

        :raises NotImplementedError: If the ``action`` attribute is not implemented in the subclass
        """
        raise NotImplementedError(
            "Subclasses of BulkUpdateBooleanFieldView must provide an 'action' attribute"
        )

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        r"""
        Update the fields of the selected objects and redirect

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """

        # Archive objects
        self.get_queryset().update(**{self.field_name: self.value})
        # Invalidate cache
        invalidate_model(self.model)
        logger.debug(
            "Updated %s=%s for %r by %r",
            self.field_name,
            self.value,
            self.get_queryset(),
            request.user,
        )
        messages.success(
            request,
            _("The selected {} were successfully {}").format(
                self.model._meta.verbose_name_plural, self.action
            ),
        )
        # Let the base view handle the redirect
        return super().post(request, *args, **kwargs)


class BulkArchiveView(BulkActionView):
    """
    Bulk action for restoring multiple objects at once
    """

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        r"""
        Archive multiple objects

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        archive_successful = []
        archive_unchanged = []
        archive_failed_because_embedded = []
        archive_failed_because_event_reference = []

        for content_object in self.get_queryset():
            title = content_object.best_translation.title
            if self.model is Page and content_object.mirroring_pages.exists():
                archive_failed_because_embedded.append(title)
            elif self.model is POI and content_object.events.count() > 0:
                archive_failed_because_event_reference.append(title)
            elif content_object.archived:
                archive_unchanged.append(title)
            else:
                content_object.archive()
                archive_successful.append(title)

        # Invalidate cache
        invalidate_model(self.model)
        logger.debug(
            "archived %r by %r",
            self.get_queryset(),
            request.user,
        )

        if archive_successful:
            messages.success(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} was successfully archived.",
                    "The following {model_name_plural} were successfully archived: {object_names}",
                    len(archive_successful),
                ).format(
                    model_name=self.model._meta.verbose_name.title(),
                    model_name_plural=self.model._meta.verbose_name_plural,
                    object_names=iter_to_string(archive_successful),
                ),
            )

        if archive_unchanged:
            messages.info(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} is already archived.",
                    "The following {model_name_plural} are already archived: {object_names}",
                    len(archive_unchanged),
                ).format(
                    model_name=self.model._meta.verbose_name.title(),
                    model_name_plural=self.model._meta.verbose_name_plural,
                    object_names=iter_to_string(archive_unchanged),
                ),
            )

        if archive_failed_because_embedded:
            messages.error(
                request,
                ngettext_lazy(
                    "Page {object_names} could not be archived because it is embedded as live content from other pages.",
                    "The following pages could not be archived because they were embedded as live content from other pages: {object_names}",
                    len(archive_failed_because_embedded),
                ).format(
                    object_names=iter_to_string(archive_failed_because_embedded),
                ),
            )

        if archive_failed_because_event_reference:
            messages.error(
                request,
                ngettext_lazy(
                    "Location {object_names} could not be archived because it is referenced by an event.",
                    "The following locations could not be archived because they were referenced by an event: {object_names}",
                    len(archive_failed_because_event_reference),
                ).format(
                    object_names=iter_to_string(archive_failed_because_event_reference),
                ),
            )

        return super().post(request, *args, **kwargs)


class BulkRestoreView(BulkActionView):
    """
    Bulk action for restoring multiple objects at once
    """

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        r"""
        Restore multiple objects

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        restore_succeeded = []
        restore_unchanged = []
        restore_failed_because_parent_archived = []

        for content_object in self.get_queryset():
            if self.get_queryset().model is Page and content_object.implicitly_archived:
                restore_failed_because_parent_archived.append(
                    content_object.best_translation.title
                )
            elif not content_object.archived:
                restore_unchanged.append(content_object.best_translation.title)
            else:
                content_object.restore()
                restore_succeeded.append(content_object.best_translation.title)

        if restore_succeeded:
            messages.success(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} was successfully restored.",
                    "The following {model_name_plural} were successfully restored: {object_names}",
                    len(restore_succeeded),
                ).format(
                    model_name=self.model._meta.verbose_name.title(),
                    model_name_plural=self.model._meta.verbose_name_plural,
                    object_names=iter_to_string(restore_succeeded),
                ),
            )

        if restore_unchanged:
            messages.success(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} is not archived.",
                    "The following {model_name_plural} are not archived: {object_names}",
                    len(restore_unchanged),
                ).format(
                    model_name=self.model._meta.verbose_name.title(),
                    model_name_plural=self.model._meta.verbose_name_plural,
                    object_names=iter_to_string(restore_unchanged),
                ),
            )

        if restore_failed_because_parent_archived:
            messages.error(
                request,
                ngettext_lazy(
                    "Page {} could not be restored because it has at least one archived parent.",
                    "The following pages could not be restored because they have at least one archived parent: {}",
                    len(restore_failed_because_parent_archived),
                ).format(
                    iter_to_string(restore_failed_because_parent_archived),
                ),
            )

        # Invalidate cache
        invalidate_model(self.model)

        return super().post(request, *args, **kwargs)


class BulkPublishingView(BulkActionView):
    """
    Bulk action to publish multiple pages at once
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Function to change the translation status to publish of multiple pages at once

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        change_publication_status(
            request, self.get_queryset(), kwargs["language_slug"], status.PUBLIC
        )
        return super().post(request, *args, **kwargs)


class BulkDraftingView(BulkActionView):
    """
    Bulk action to draft multiple pages at once
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Function to change the translation status to draft of multiple pages at once

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        change_publication_status(
            request, self.get_queryset(), kwargs["language_slug"], status.DRAFT
        )
        return super().post(request, *args, **kwargs)
