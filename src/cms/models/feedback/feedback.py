from django.conf import settings
from django.db import models
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from ...constants import feedback_ratings
from ...utils.translation_utils import ugettext_many_lazy as __
from ..languages.language import Language
from ..regions.region import Region


class Feedback(models.Model):
    """
    Database model representing feedback from app-users.
    Do not directly create instances of this base model, but of the submodels (e.g. PageFeedback) instead.
    """

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("region"),
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("language"),
    )
    #: Manage choices in :mod:`cms.constants.feedback_ratings`
    rating = models.BooleanField(
        null=True,
        blank=True,
        default=feedback_ratings.NOT_STATED,
        choices=feedback_ratings.CHOICES,
        verbose_name=_("rating"),
        help_text=_("Whether the feedback is positive or negative"),
    )
    comment = models.TextField(blank=True, verbose_name=_("comment"))
    is_technical = models.BooleanField(
        verbose_name=_("technical"),
        help_text=_("Whether or not the feedback is targeted at the developers"),
    )
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="feedback",
        verbose_name=_("marked as read by"),
        help_text=__(
            _("The user who marked this feedback as read."),
            _("If the feedback is unread, this field is empty."),
        ),
    )
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("creation date"),
    )

    @property
    def submodel_instance(self):
        """
        This property returns the submodel instance (e.g. PageFeedback) of a Feedback instance.
        """
        # In this case we need type() instead of isinstance(), because we want to differ between inherited models
        # pylint: disable=unidiomatic-typecheck
        if type(self) != Feedback:
            raise NotImplementedError(
                "Use submodel_instance only on instances of the base Feedback model, not on submodels."
            )
        for submodel in Feedback.__subclasses__():
            # Inherited models automatically get their name as lowercase assigned as reverse relationship from the base class
            reverse_related_name = submodel.__name__.lower()
            if hasattr(self, reverse_related_name):
                return getattr(self, reverse_related_name)
        raise TypeError(
            "Do not directly create instances of the Feedback base model, but of the submodels (e.g. PageFeedback) instead."
        )

    @property
    def category(self):
        """
        This property returns the category (verbose name of the submodel) of this feedback object.
        """
        return capfirst(type(self.submodel_instance)._meta.verbose_name)

    @property
    def object_name(self):
        """
        This property returns the name of the object this feedback comments on.
        To be implemented in the inheriting model.
        """
        return self.submodel_instance.object_name

    @property
    def object_url(self):
        """
        This property returns the url to the object this feedback comments on.
        To be implemented in the inheriting model.
        """
        return self.submodel_instance.object_url

    @property
    def related_feedback(self):
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        :rtype: ~django.db.models.query.QuerySet [ ~cms.models.feedback.feedback.Feedback ]
        """
        return self.submodel_instance.related_feedback

    @property
    def rating_sum_positive(self):
        """
        This property returns the sum of the up-ratings of this object.

        :return: The number of positive ratings on this feedback object
        :rtype: int
        """
        # Enable this property on instances of the base Feedback model
        # In this case we need type() instead of isinstance(), because we want to differ between inherited models
        # pylint: disable=unidiomatic-typecheck
        if type(self) == Feedback:
            instance = self.submodel_instance
        else:
            instance = self
        return instance.related_feedback.filter(
            rating=feedback_ratings.POSITIVE
        ).count()

    @property
    def rating_sum_negative(self):
        """
        This property returns the sum of the down-ratings of this object.

        :return: The number of negative ratings on this feedback object
        :rtype: int
        """
        # Enable this property on instances of the base Feedback model
        # In this case we need type() instead of isinstance(), because we want to differ between inherited models
        # pylint: disable=unidiomatic-typecheck
        if type(self) == Feedback:
            instance = self.submodel_instance
        else:
            instance = self
        return instance.related_feedback.filter(
            rating=feedback_ratings.NEGATIVE
        ).count()

    @property
    def read(self):
        """
        This property returns whether or not the feedback is marked as read or not.
        It is ``True`` if :attr:`~cms.models.feedback.feedback.Feedback.read_by` is set and ``False`` otherwise.
        """
        return bool(self.read_by)

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Feedback object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the feedback
        :rtype: str
        """
        return self.comment

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Feedback: Feedback object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the feedback
        :rtype: str
        """
        # pylint: disable=unidiomatic-typecheck
        if type(self) == Feedback:
            class_name = type(self.submodel_instance).__name__
        else:
            class_name = type(self).__name__
        return f"<{class_name} (id: {self.id})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("feedback")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["-created_date"]
        #: The default permissions for this model
        default_permissions = ()
        #:  The custom permissions for this model
        permissions = (("manage_feedback", "Can manage feedback"),)
