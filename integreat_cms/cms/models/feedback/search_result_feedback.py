from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from .feedback import Feedback


class SearchResultFeedback(Feedback):
    """
    Database model representing feedback about search results (e.g. empty results).
    """

    search_query = models.CharField(max_length=1000, verbose_name=_("search term"))

    @property
    def object_name(self):
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        :rtype: str
        """
        return _("Search results for {}").format(self.search_query)

    @cached_property
    def object_url(self):
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        :rtype: str
        """
        return ""

    @property
    def related_feedback(self):
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.feedback.search_result_feedback.SearchResultFeedback ]
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
