from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import PageFilterForm
from ...models import PageTranslation
from ..mixins import MachineTranslationContextMixin
from .page_context_mixin import PageContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_page"), name="dispatch")
class PageTreeView(TemplateView, PageContextMixin, MachineTranslationContextMixin):
    """
    View for showing the page tree
    """

    #: Template for list of non-archived pages
    template = "pages/page_tree.html"
    #: Template for list of archived pages
    template_archived = "pages/page_tree_archived.html"
    #: Whether or not to show archived pages
    archived = False
    #: The translation model of this list view (used to determine whether machine translations are permitted)
    translation_model = PageTranslation

    @property
    def template_name(self) -> str:
        """
        Select correct HTML template, depending on :attr:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView.archived` flag
        (see :class:`~django.views.generic.base.TemplateResponseMixin`)

        :return: Path to HTML template
        """

        return self.template_archived if self.archived else self.template

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render page tree

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        # current region
        region = request.region

        # current language
        if language_slug := kwargs.get("language_slug"):
            language = region.get_language_or_404(language_slug, only_active=True)
        elif region.default_language:
            return redirect(
                "pages",
                **{
                    "region_slug": region.slug,
                    "language_slug": region.default_language.slug,
                },
            )
        else:
            messages.error(
                request,
                _("Please create at least one language node before creating pages."),
            )
            return redirect(
                "languagetreenodes",
                **{
                    "region_slug": region.slug,
                },
            )

        if not request.user.has_perm("cms.change_page"):
            access_granted_pages = request.user.access_granted_pages(request.region)
            if len(access_granted_pages) > 0:
                messages.info(
                    request,
                    format_html(
                        "{}<ul class='list-disc pl-4'>{}</ul>",
                        _("You can edit only those pages: "),
                        format_html_join(
                            "\n",
                            "<li><a href='{}' class='underline hover:no-underline'>{}</a></li>",
                            [
                                (
                                    page.best_translation.backend_edit_link,
                                    page.best_translation.title,
                                )
                                for page in access_granted_pages
                            ],
                        ),
                    ),
                )
            else:
                messages.warning(
                    request, _("You don't have the permission to edit or create pages.")
                )

        # Initialize page filter form
        filter_form = PageFilterForm(data=request.GET)

        page_queryset = (
            # If filters are applied or only archived pages are requested, fetch all elements from the database
            region.pages.all()
            if filter_form.is_enabled or self.archived
            # Else, only fetch the root pages and load the subpages dynamically via ajax
            else region.pages.filter(lft=1)
        )

        # Cache tree structure to reduce database queries
        pages = (
            page_queryset.prefetch_major_translations()
            .prefetch_related("mirroring_pages")
            .cache_tree(archived=self.archived)
        )

        # Filter pages according to given filters, if any
        pages = filter_form.apply(pages, language_slug)
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "pages": pages,
                "language": language,
                "source_language": region.get_source_language(language.slug),
                "content_type": "page",
                "languages": region.active_languages,
                "textlab_languages": settings.TEXTLAB_API_LANGUAGES,
                "filter_form": filter_form,
                "XLIFF_EXPORT_VERSION": settings.XLIFF_EXPORT_VERSION,
                "hix_threshold": settings.HIX_REQUIRED_FOR_MT,
            },
        )
