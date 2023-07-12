import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Case, Exists, F, OuterRef, Subquery, When
from django.utils import translation
from django.views.generic import TemplateView

from ...constants import status
from ...models import Feedback, Page, PageTranslation
from ...utils.linkcheck_utils import filter_urls
from ..chat.chat_context_mixin import ChatContextMixin

logger = logging.getLogger(__name__)


class DashboardView(TemplateView, ChatContextMixin):
    """
    View for the region dashboard
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        r"""
        Extend context by blog urls

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The context dictionary
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        # RSS FEED urls
        language_slug = translation.get_language()
        context.update(
            {
                "current_menu_item": "region_dashboard",
                "blog_url": settings.BLOG_URLS.get(
                    language_slug, settings.DEFAULT_BLOG_URL
                ),
                "feed_url": settings.RSS_FEED_URLS.get(
                    language_slug, settings.DEFAULT_RSS_FEED_URL
                ),
            }
        )

        context.update(self.get_unreviewed_pages_context())
        context.update(self.get_automatically_saved_pages())
        context.update(self.get_unread_feedback_context())
        context.update(self.get_broken_links_context())
        context.update(self.get_low_hix_value_context())
        context.update(self.get_outdated_pages_context())
        return context

    def get_unreviewed_pages_context(self):
        """
        Extend context by info on unreviewed pages

        :return: Dictionary containing the context for unreviewed pages
        :rtype: dict
        """

        explicitly_archived_ancestors = Page.objects.filter(
            tree_id=OuterRef("pk"),
            lft__lt=OuterRef("lft"),
            rgt__gt=OuterRef("rgt"),
            explicitly_archived=True,
        ).values("pk")

        not_implicitly_archived_ids = Page.objects.filter(
            id=Case(
                When(
                    Exists(explicitly_archived_ancestors),
                    then=None,
                ),
                default=F("pk"),
            )
        )

        unreviewed_pages = (
            PageTranslation.objects.filter(
                page__region=self.request.region,
                status=status.REVIEW,
                page__explicitly_archived=False,
                language__slug=self.request.region.default_language.slug,
                page__id__in=Subquery(not_implicitly_archived_ids.values("pk")),
            )
            .order_by("page__id", "language__id", "-version")
            .distinct("page__id", "language__id")
            .all()
        )

        return {
            "unreviewed_pages": unreviewed_pages,
            "default_language_slug": self.request.region.default_language.slug,
        }

    def get_automatically_saved_pages(self):
        r"""
        Extend context by info on automatically saved pages

        :return: Dictionary containing the context for auto saved pages
        :rtype: dict
        """
        explicitly_archived_ancestors = Page.objects.filter(
            tree_id=OuterRef("pk"),
            lft__lt=OuterRef("lft"),
            rgt__gt=OuterRef("rgt"),
            explicitly_archived=True,
        ).values("pk")

        not_implicitly_archived_ids = Page.objects.filter(
            id=Case(
                When(
                    Exists(explicitly_archived_ancestors),
                    then=None,
                ),
                default=F("pk"),
            )
        )

        last_versions = (
            PageTranslation.objects.filter(
                page__explicitly_archived=False,
                page__id__in=Subquery(not_implicitly_archived_ids.values("pk")),
                page__region=self.request.region,
                language__slug=self.request.region.default_language.slug,
            )
            .order_by("page__id", "language__id", "-version")
            .distinct("page__id", "language__id")
        )

        automatically_saved_pages = PageTranslation.objects.filter(
            id__in=Subquery(last_versions.values("pk")),
            status=status.AUTO_SAVE,
        )

        return {
            "automatically_saved_pages": automatically_saved_pages,
            "default_language_slug": self.request.region.default_language.slug,
        }

    def get_unread_feedback_context(self):
        r"""
        Extend context by info on unread feedback

        :return: Dictionary containing the context for unreviewed pages
        :rtype: dict
        """
        unread_feedback = Feedback.objects.filter(
            read_by=None, archived=False, region=self.request.region
        )
        return {
            "unread_feedback": unread_feedback,
        }

    def get_broken_links_context(self):
        r"""
        Extend context by info on broken links

        :return: Dictionary containing the context for broken links
        :rtype: dict
        """
        invalid_urls = filter_urls(self.request.region.slug, "invalid")[0]
        invalid_url = invalid_urls[0] if invalid_urls else None

        relevant_translation = (
            invalid_url.region_links[0].content_object if invalid_url else None
        )

        return {
            "broken_links": invalid_urls,
            "relevant_translation": relevant_translation,
            "relevant_url": invalid_url,
        }

    def get_low_hix_value_context(self):
        r"""
        Extend context by info on pages with low hix value

        :return: Dictionary containing the context for pages with low hix value
        :rtype: dict
        """
        pages_under_hix_threshold = []
        if settings.TEXTLAB_API_ENABLED and self.request.region.hix_enabled:
            hix_pages = self.request.region.get_pages(
                return_unrestricted_queryset=True
            ).filter(hix_ignore=False)
            hix_translations = PageTranslation.objects.filter(
                language__slug__in=settings.TEXTLAB_API_LANGUAGES, page__in=hix_pages
            ).distinct("page_id", "language_id")

            for hix_translation in hix_translations:
                if (
                    hix_translation.hix_score is not None
                    and hix_translation.hix_score < settings.HIX_REQUIRED_FOR_MT
                ):
                    pages_under_hix_threshold.append(hix_translation)

            return {
                "pages_under_hix_threshold": pages_under_hix_threshold,
            }
        return {}

    def get_outdated_pages_context(self):
        r"""
        Extend context by info on outdated pages

        :return: Dictionary containing the context for outdated pages
        :rtype: dict
        """
        OUTDATED_THRESHOLD_DATE = datetime.now() - relativedelta(
            days=settings.OUTDATED_THRESHOLD_DAYS
        )

        explicitly_archived_ancestors = Page.objects.filter(
            tree_id=OuterRef("pk"),
            lft__lt=OuterRef("lft"),
            rgt__gt=OuterRef("rgt"),
            explicitly_archived=True,
        ).values("pk")

        not_implicitly_archived_ids = Page.objects.filter(
            id=Case(
                When(
                    Exists(explicitly_archived_ancestors),
                    then=None,
                ),
                default=F("pk"),
            )
        )

        last_versions = (
            PageTranslation.objects.filter(
                page__region=self.request.region,
                page__explicitly_archived=False,
                page__id__in=Subquery(not_implicitly_archived_ids.values("pk")),
                language__slug=self.request.region.default_language.slug,
            )
            .order_by("page__id", "language__id", "-version", "last_updated")
            .distinct("page__id", "language__id")
        )

        outdated_pages = PageTranslation.objects.filter(
            id__in=Subquery(last_versions.values("pk")),
            last_updated__lte=OUTDATED_THRESHOLD_DATE.date(),
        )

        # print(outdated_pages)

        days_since_last_updated = (
            (
                datetime.today() - most_outdated_page.last_updated.replace(tzinfo=None)
            ).days
            if (most_outdated_page := outdated_pages[0] if outdated_pages else None)
            else None
        )

        OUTDATED_THRESHOLD_DATE = OUTDATED_THRESHOLD_DATE.strftime("%Y-%m-%d")

        return {
            "outdated_pages": outdated_pages,
            "most_outdated_page": most_outdated_page,
            "days_since_last_updated": days_since_last_updated,
            "outdated_threshold_date": OUTDATED_THRESHOLD_DATE,
        }
