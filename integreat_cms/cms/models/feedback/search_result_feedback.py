from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .feedback import Feedback

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class SearchResultFeedback(Feedback):
    """
    Database model representing feedback about search results (e.g. empty results).
    """

    search_query = models.CharField(max_length=1000, verbose_name=_("search term"))

    @property
    def object_name(self) -> str:
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        """
        return _("Search results for {}").format(self.search_query)

    @cached_property
    def object_url(self) -> str:
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        """
        return ""

    @property
    def related_feedback(self) -> QuerySet[SearchResultFeedback]:
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        """
        return SearchResultFeedback.objects.filter(
            region=self.region,
            language=self.language,
            search_query=self.search_query,
            is_technical=self.is_technical,
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("search result feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("search result feedback")
        #: The default permissions for this model
        default_permissions = ()
