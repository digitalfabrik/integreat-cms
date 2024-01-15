from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.generic.list import MultipleObjectMixin

from ....xliff.utils import pages_to_xliff_file
from ...models import Page
from ...utils.pdf_utils import generate_pdf
from ...utils.translation_utils import gettext_many_lazy as __
from ...utils.translation_utils import translate_link
from ..bulk_action_views import BulkActionView

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
        self, request: HttpRequest, *args: Any, **kwargs: Any
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


class ExportXliffView(PageBulkActionMixin, BulkActionView):
    """
    Bulk action for generating XLIFF files for translations
    """

    #: Whether only public translation should be exported
    only_public = False
    #: Whether the view requires change permissions
    require_change_permission = False

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
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
                        "XLIFF file with published pages only for translation to {} successfully created."
                    )
                    if self.only_public
                    else _(
                        "XLIFF file with unpublished and published pages for translation to {} successfully created."
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
            request, self.get_queryset(), target_languages, only_public=False
        ):
            # Insert link with automatic download into success message
            message = __(
                _(
                    "XLIFF file for translation to selected languages successfully created."
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
