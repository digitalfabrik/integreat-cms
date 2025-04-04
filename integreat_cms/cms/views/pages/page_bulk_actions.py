from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext, ngettext_lazy
from django.views.decorators.cache import never_cache
from django.views.generic.list import MultipleObjectMixin

from ....xliff.utils import pages_to_xliff_file
from ...constants import translation_status
from ...models import Page
from ...utils.pdf_utils import generate_pdf
from ...utils.stringify_list import iter_to_string
from ...utils.translation_utils import gettext_many_lazy as __
from ...utils.translation_utils import translate_link
from ..bulk_action_views import BulkActionView, BulkArchiveView
from .page_actions import cancel_translation_process_ajax

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse
    from django.http.response import HttpResponseRedirect

logger = logging.getLogger(__name__)


class PageBulkActionMixin(MultipleObjectMixin):
    """
    Mixin for page bulk actions
    """

    #: The model of this :class:`~integreat_cms.cms.views.bulk_action_views.BulkActionView`
    model = Page


class GeneratePdfView(PageBulkActionMixin, BulkActionView):
    """
    Bulk action for generating a PDF document of the content
    """

    #: Whether the view requires change permissions
    require_change_permission = False
    #: Whether the public translation objects should be prefetched
    prefetch_public_translations = True

    @method_decorator(never_cache)
    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseRedirect:
        r"""
        Apply the bulk action on every item in the queryset and redirect

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        # Generate PDF document and redirect to it
        return generate_pdf(
            request.region,
            str(kwargs.get("language_slug")),
            self.get_queryset(),
        )


class PageBulkArchiveView(PageBulkActionMixin, BulkArchiveView):
    """
    Bulk action for archiving multiple pages at once
    """

    def get_permission_required(self) -> tuple[str]:
        return ("cms.publish_page_object",)


class ExportXliffView(PageBulkActionMixin, BulkActionView):
    """
    Bulk action for generating XLIFF files for translations
    """

    #: Whether only public translation should be exported
    only_public = False
    #: Whether the view requires change permissions
    require_change_permission = False

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseRedirect:
        r"""
        Function for handling a XLIFF export request for pages.
        The pages get extracted from request.GET attribute and the request is forwarded to :func:`~integreat_cms.xliff.utils.pages_to_xliff_file`

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """
        target_language = get_object_or_404(
            self.request.region.language_tree_nodes,
            language__slug=kwargs.get("language_slug"),
            parent__isnull=False,
        ).language

        if xliff_file_url := pages_to_xliff_file(
            request,
            self.get_queryset(),
            [target_language],
            only_public=self.only_public,
        ):
            # Insert link with automatic download into success message
            message = __(
                (
                    _(
                        "XLIFF file with published pages only for translation to {} successfully created.",
                    )
                    if self.only_public
                    else _(
                        "XLIFF file with unpublished and published pages for translation to {} successfully created.",
                    )
                ).format(target_language),
                _(
                    "If the download does not start automatically, please click <a>here</a>.",
                ),
            )
            messages.success(
                request,
                translate_link(
                    message,
                    attributes={
                        "href": xliff_file_url,
                        "class": "font-bold underline hover:no-underline",
                        "data-auto-download": "",
                        "download": "",
                    },
                ),
            )

        # Let the base view handle the redirect
        return super().post(request, *args, **kwargs)


class ExportMultiLanguageXliffView(PageBulkActionMixin, BulkActionView):
    """
    Bulk action for generating XLIFF files for translations in multiple languages.
    """

    #: Whether the view requires change permissions
    require_change_permission = False

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Function for handling a XLIFF export request for pages and multiple languages.
        The pages get extracted from request.GET attribute and the request is forwarded to :func:`~integreat_cms.xliff.utils.pages_to_xliff_file`

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """

        target_languages = [
            language
            for language in self.request.region.active_languages
            if language.slug in self.request.POST.getlist("selected_language_slugs[]")
        ]

        if xliff_file_url := pages_to_xliff_file(
            request,
            self.get_queryset(),
            target_languages,
            only_public=False,
        ):
            # Insert link with automatic download into success message
            message = __(
                _(
                    "XLIFF file for translation to selected languages successfully created.",
                ),
                _(
                    "If the download does not start automatically, please click <a>here</a>.",
                ),
            )
            messages.success(
                request,
                translate_link(
                    message,
                    attributes={
                        "href": xliff_file_url,
                        "class": "font-bold underline hover:no-underline",
                        "data-auto-download": "",
                        "download": "",
                    },
                ),
            )

        # Let the base view handle the redirect
        return super().post(request, *args, **kwargs)


class CancelTranslationProcess(PageBulkActionMixin, BulkActionView):
    """
    Bulk action to cancel translation process
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Function to cancel the translation process for multiple pages of the current language at once

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The redirect
        """

        language_slug = kwargs["language_slug"]
        not_in_translation = []
        cancel_successful = []
        cancel_failed = []

        for content_object in self.get_queryset():
            if (
                content_object.get_translation_state(language_slug)
                != translation_status.IN_TRANSLATION
            ):
                not_in_translation.append(content_object.best_translation.title)
            else:
                cancelation_response = cancel_translation_process_ajax(
                    request,
                    region_slug=content_object.region,
                    language_slug=language_slug,
                    page_id=content_object.id,
                )
                if cancelation_response.status_code == 200:
                    cancel_successful.append(content_object.best_translation.title)
                if cancelation_response.status_code == 404:
                    cancel_failed.append(content_object.best_translation.title)

        if not_in_translation:
            messages.success(
                request,
                ngettext_lazy(
                    "{model_name} {object_names} was not in translation process.",
                    "The following {model_name} were not in translation process: {object_names}",
                    len(not_in_translation),
                ).format(
                    model_name=ngettext(
                        self.model._meta.verbose_name.title(),
                        self.model._meta.verbose_name_plural,
                        len(not_in_translation),
                    ),
                    object_names=iter_to_string(not_in_translation),
                ),
            )
        if cancel_successful:
            messages.success(
                request,
                ngettext_lazy(
                    "Translation process was successfully cancelled for {model_name} {object_names}.",
                    "Translation process was successfully cancelled for the following {model_name}: {object_names}",
                    len(cancel_successful),
                ).format(
                    model_name=ngettext(
                        self.model._meta.verbose_name.title(),
                        self.model._meta.verbose_name_plural,
                        len(cancel_successful),
                    ),
                    object_names=iter_to_string(cancel_successful),
                ),
            )

        if cancel_failed:
            messages.error(
                request,
                ngettext_lazy(
                    "Translation process could not be successfully cancelled for {model_name} {object_names}.",
                    "Translation process could not be successfully cancelled for the following {model_name}: {object_names}",
                    len(cancel_failed),
                ).format(
                    model_name=ngettext(
                        self.model._meta.verbose_name.title(),
                        self.model._meta.verbose_name_plural,
                        len(cancel_failed),
                    ),
                    object_names=iter_to_string(cancel_failed),
                ),
            )
        return super().post(request, *args, **kwargs)
