from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Q, Subquery
from django.http import JsonResponse
from django.urls import reverse
from django.utils import translation
from django.views.generic import TemplateView

from ....api.decorators import json_response
from ...constants import status
from ...models import Feedback, PageTranslation
from ...utils.linkcheck_utils import filter_urls
from ..chat.chat_context_mixin import ChatContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.query import QuerySet
    from django.http import HttpRequest
    from linkcheck.models import Url

    from ...models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)


class DashboardView(TemplateView, ChatContextMixin):
    """
    View for the region dashboard
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name: str = "dashboard/dashboard.html"
    #: The ids of the latest page translations of the current region
    latest_version_ids: list[int] = []

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Extend context by blog urls

        :param \**kwargs: The supplied keyword arguments
        :return: The context dictionary
        """
        context = super().get_context_data(**kwargs)
        # RSS FEED urls
        language_slug = translation.get_language()
        self.latest_version_ids = self.get_latest_versions()
        context.update(
            {
                "current_menu_item": "region_dashboard",
                "blog_url": settings.BLOG_URLS.get(
                    language_slug, settings.DEFAULT_BLOG_URL
                ),
                "feed_url": settings.RSS_FEED_URLS.get(
                    language_slug, settings.DEFAULT_RSS_FEED_URL
                ),
                "broken_link_ajax": reverse(
                    "get_broken_links_ajax",
                    kwargs={"region_slug": self.request.region.slug},
                ),
            }
        )

        context.update(self.get_unreviewed_pages_context())
        context.update(self.get_automatically_saved_pages())
        context.update(self.get_unread_feedback_context())
        context.update(self.get_low_hix_value_context())
        context.update(self.get_outdated_pages_context())
        context.update(self.get_drafted_pages())

        return context

    def get_latest_versions(self) -> list[int]:
        """
        Collects all the latest page translations of the current region

        :return: The ids of the latest page translations of the current region
        """
        latest_version_ids = (
            PageTranslation.objects.filter(
                page__id__in=Subquery(
                    self.request.region.non_archived_pages.values("pk")
                ),
            )
            .distinct("page__id", "language__id")
            .values_list("pk", flat=True)
        )
        return list(latest_version_ids)

    def get_unreviewed_pages_context(self) -> dict[str, QuerySet | str]:
        """
        Extend context by info on unreviewed pages

        :return: Dictionary containing the context for unreviewed pages
        """
        if not self.request.region.default_language:
            return {}

        unreviewed_pages = PageTranslation.objects.filter(
            language__slug=self.request.region.default_language.slug,
            id__in=self.latest_version_ids,
            status=status.REVIEW,
        )

        return {
            "unreviewed_pages": unreviewed_pages,
            "default_language_slug": self.request.region.default_language.slug,
        }

    def get_automatically_saved_pages(self) -> dict[str, QuerySet | str]:
        r"""
        Extend context by info on automatically saved pages

        :return: Dictionary containing the context for auto saved pages
        """
        if not self.request.region.default_language:
            return {}

        automatically_saved_pages = PageTranslation.objects.filter(
            language__slug=self.request.region.default_language.slug,
            id__in=self.latest_version_ids,
            status=status.AUTO_SAVE,
        )

        return {
            "automatically_saved_pages": automatically_saved_pages,
            "default_language_slug": self.request.region.default_language.slug,
        }

    def get_unread_feedback_context(self) -> dict[str, QuerySet]:
        r"""
        Extend context by info on unread feedback

        :return: Dictionary containing the context for unreviewed pages
        """
        unread_feedback = Feedback.objects.filter(
            read_by=None, archived=False, region=self.request.region
        )
        return {
            "unread_feedback": unread_feedback,
        }

    @json_response
    # pylint: disable=unused-argument, disable=no-self-argument
    def get_broken_links_context(
        request: HttpRequest, region_slug: str
    ) -> JsonResponse:
        r"""
        Extend context by info on broken links

        :return: Dictionary containing the context for broken links
        """
        invalid_urls = filter_urls(request.region.slug, "invalid")[0]
        invalid_url = invalid_urls[0] if invalid_urls else None

        relevant_translation = (
            invalid_url.region_links[0].content_object if invalid_url else None
        )

        edit_url = (
            reverse(
                "edit_url",
                kwargs={
                    "region_slug": request.region.slug,
                    "url_filter": "invalid",
                    "url_id": invalid_url.pk,
                },
            )
            if invalid_url
            else ""
        )

        return JsonResponse(
            data={
                "broken_links": len(invalid_urls),
                "relevant_translation": str(relevant_translation),
                "edit_url": f"{edit_url}" if len(edit_url) > 0 else "",
            }
        )

    def get_low_hix_value_context(self) -> dict[str, list[PageTranslation]]:
        r"""
        Extend context by info on pages with low hix value

        :return: Dictionary containing the context for pages with low hix value
        """
        if not settings.TEXTLAB_API_ENABLED or not self.request.region.hix_enabled:
            return {}

        translations = PageTranslation.objects.filter(
            language__slug__in=settings.TEXTLAB_API_LANGUAGES,
            id__in=self.latest_version_ids,
            page__hix_ignore=False,
            hix_score__lt=settings.HIX_REQUIRED_FOR_MT,
        )

        translations_under_hix_threshold = [
            translation
            for translation in translations
            if not translation.hix_sufficient_for_mt
        ]

        return {
            "pages_under_hix_threshold": translations_under_hix_threshold,
        }

    def get_outdated_pages_context(
        self,
    ) -> dict[str, QuerySet | PageTranslation | datetime | int | None]:
        r"""
        Extend context by info on outdated pages

        :return: Dictionary containing the context for outdated pages
        """
        if not self.request.region.default_language:
            return {}

        outdated_threshold_date = datetime.now() - relativedelta(
            days=settings.OUTDATED_THRESHOLD_DAYS
        )

        outdated_pages = (
            PageTranslation.objects.filter(
                language__slug=self.request.region.default_language.slug,
                id__in=self.latest_version_ids,
                last_updated__lte=outdated_threshold_date.date(),
                status=status.PUBLIC,
            )
            .order_by("last_updated")
            .exclude(Q(content="") & Q(page__mirrored_page=None))
        )

        days_since_last_updated = (
            (datetime.now() - most_outdated_page.last_updated.replace(tzinfo=None)).days
            if (most_outdated_page := outdated_pages[0] if outdated_pages else None)
            else None
        )

        outdated_threshold_date_str = outdated_threshold_date.strftime("%Y-%m-%d")

        return {
            "outdated_pages": outdated_pages,
            "most_outdated_page": most_outdated_page,
            "days_since_last_updated": days_since_last_updated,
            "outdated_threshold_date": outdated_threshold_date_str,
        }

    def get_drafted_pages(
        self,
    ) -> dict[str, QuerySet]:
        r"""
        Extend context by info on drafted pages

        :return: Dictionary containing the context for drafted pages for one region.
        """
        if not self.request.region.default_language:
            return {}

        drafted_pages = PageTranslation.objects.filter(
            id__in=self.latest_version_ids,
            status=status.DRAFT,
            language__slug=self.request.region.default_language.slug,
        )
        single_drafted_page = drafted_pages.first()
        return {
            "drafted_pages": drafted_pages,
            "single_drafted_page": single_drafted_page,
        }
