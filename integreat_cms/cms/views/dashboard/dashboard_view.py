import logging

from django.conf import settings
from django.utils import translation
from django.views.generic import TemplateView

from ...models import PageTranslation
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
        context.update(self.get_hix_context())
        return context

    def get_hix_context(self):
        """
        Extend context by HIX info

        :return: The HIX context dictionary
        :rtype: dict
        """
        if not settings.TEXTLAB_API_ENABLED:
            return {}

        # Get the current region
        region = self.request.region
        if not region.hix_enabled:
            return {}

        # Get all pages of this region which are considered for the HIX value
        hix_pages = region.get_pages(return_unrestricted_queryset=True).filter(
            hix_ignore=False
        )

        # Get the latest versions of the page translations for these pages
        hix_translations = PageTranslation.objects.filter(
            language__slug__in=settings.TEXTLAB_API_LANGUAGES, page__in=hix_pages
        ).distinct("page_id", "language_id")

        # Get all hix translations where the score is set
        hix_translations_with_score = [pt for pt in hix_translations if pt.hix_score]

        # Get the worst n pages
        worst_hix_translations = sorted(
            hix_translations_with_score, key=lambda pt: pt.hix_score
        )

        # Get the number of translations which are not ready for MT
        not_ready_for_mt_count = sum(
            pt.hix_score < settings.HIX_REQUIRED_FOR_MT
            for pt in hix_translations_with_score
        )

        return {
            "worst_hix_translations": worst_hix_translations,
            "hix_threshold": settings.HIX_REQUIRED_FOR_MT,
            "ready_for_mt_count": len(hix_translations) - not_ready_for_mt_count,
            "total_count": len(hix_translations),
        }
