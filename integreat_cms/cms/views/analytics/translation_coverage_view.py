from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...constants.translation_status import (
    CHOICES,
    COLORS,
    MISSING,
    OUTDATED,
)
from ...decorators import permission_required
from ...views.utils.hix import (
    get_translation_under_hix_threshold,
    get_translations_relevant_to_hix,
)
from ..utils import get_translation_and_word_count

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.query import QuerySet


logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_translation_report"), name="dispatch")
class TranslationCoverageView(TemplateView):
    """
    View to calculate and show the translation coverage statistics (up to date translations, missing translation, etc)
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "analytics/translation_coverage.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Extend context by translation coverage data

        :param \**kwargs: The supplied keyword arguments
        :return: The context dictionary
        """
        # The current region
        region = self.request.region

        translation_count, word_count = get_translation_and_word_count(region)

        logger.debug("Translation status count: %r", translation_count)
        logger.debug("Word count: %r", word_count)
        # Assemble the ChartData in the format expected by ChartJS (one dataset for each translation status)
        chart_data = {
            "labels": [language.translated_name for language in translation_count],
            "datasets": [
                {
                    "label": label,
                    "backgroundColor": COLORS[status],
                    "data": [data[status] for data in translation_count.values()],
                }
                for status, label in CHOICES
            ],
        }
        # Update and return the template context
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_menu_item": "translation_coverage",
                "chart_data": chart_data,
                "word_count": word_count,
                "total_outdated_words": sum(c[OUTDATED] for c in word_count.values()),
                "total_missing_words": sum(c[MISSING] for c in word_count.values()),
            },
        )
        context.update(self.get_hix_context())
        return context

    def get_hix_context(self) -> dict[str, QuerySet | int | float]:
        """
        Extend context by HIX info

        :return: The HIX context dictionary
        """
        # We want to calculate page translations with hix_score=None, but not show them
        # That's why we have to exclude them here.
        relevant_translations = (
            get_translations_relevant_to_hix(self.request.region)
            .exclude(hix_score=None)
            .prefetch_related("page")
        )

        translations_under_hix_threshold = get_translation_under_hix_threshold(
            self.request.region,
        ).count()

        total_count = get_translations_relevant_to_hix(self.request.region).count()

        return {
            "worst_hix_translations": relevant_translations,
            "hix_threshold": settings.HIX_REQUIRED_FOR_MT,
            "ready_for_mt_count": total_count - translations_under_hix_threshold,
            "total_count": total_count,
        }
