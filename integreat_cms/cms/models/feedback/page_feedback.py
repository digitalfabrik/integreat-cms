from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from ..pages.page_translation import PageTranslation
from .feedback import Feedback


class PageFeedback(Feedback):
    """
    Database model representing feedback about pages.
    """

    page_translation = models.ForeignKey(
        PageTranslation,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("page translation"),
    )

    @property
    def object_name(self):
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        :rtype: str
        """
        return self.best_page_translation.title

    @cached_property
    def object_url(self):
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        :rtype: str
        """
        return reverse(
            "edit_page",
            kwargs={
                "page_id": self.page_translation.page.id,
                "region_slug": self.region.slug,
                "language_slug": self.best_page_translation.language.slug,
            },
        )

    @cached_property
    def best_page_translation(self):
        """
        This property returns the best translation for the page this feedback comments on.

        :return: The best page translation
        :rtype: ~integreat_cms.cms.models.pages.page_translation.PageTranslation
        """
        return self.page_translation.page.best_translation

    @property
    def related_feedback(self):
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.feedback.page_feedback.PageFeedback ]
        """
        return PageFeedback.objects.filter(
            page_translation__page=self.page_translation.page,
            language=self.language,
            is_technical=self.is_technical,
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("page feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("page feedback")
        #: The default permissions for this model
        default_permissions = ()
