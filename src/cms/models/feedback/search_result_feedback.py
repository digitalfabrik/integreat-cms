from django.db import models
from django.utils.translation import ugettext_lazy as _

from .feedback import Feedback
from ..regions.region import Region


class SearchResultFeedback(Feedback):
    """
    Database model representing feedback about search results (e.g. empty results).
    """

    searchQuery = models.CharField(max_length=1000, verbose_name=_("search term"))
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="search_result_feedback",
        verbose_name=_("region"),
    )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("search result feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("search result feedback")
        #: The default permissions for this model
        default_permissions = ()
