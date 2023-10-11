from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet
from polymorphic.models import PolymorphicModel

from ...constants import feedback_ratings
from ...utils.translation_utils import gettext_many_lazy as __
from ..abstract_base_model import AbstractBaseModel
from ..languages.language import Language
from ..regions.region import Region

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class CascadeDeletePolymorphicQuerySet(PolymorphicQuerySet):
    """
    Patch the QuerySet to call delete on the non_polymorphic QuerySet, avoiding models.deletion.Collector typing problem

    Based on workarounds proposed in: https://github.com/django-polymorphic/django-polymorphic/issues/229
    See also: https://github.com/django-polymorphic/django-polymorphic/issues/34, https://github.com/django-polymorphic/django-polymorphic/issues/84
    Related Django ticket: https://code.djangoproject.com/ticket/23076
    """

    def delete(self) -> tuple[int, dict[str, int]]:
        """
        This method deletes all objects in this QuerySet.

        :return: A tuple of the number of objects delete and the delete objects grouped by their type
        """
        if not self.polymorphic_disabled:
            return self.non_polymorphic().delete()

        return super().delete()


class CascadeDeletePolymorphicManager(PolymorphicManager):
    """
    This class is used as a workaround for a bug in django-polymorphic.
    For more information, see :class:`~integreat_cms.cms.models.feedback.feedback.CascadeDeletePolymorphicQuerySet`.
    """

    queryset_class = CascadeDeletePolymorphicQuerySet


class Feedback(PolymorphicModel, AbstractBaseModel):
    """
    Database model representing feedback from app-users.
    Do not directly create instances of this base model, but of the submodels (e.g. PageFeedback) instead.
    """

    objects = CascadeDeletePolymorphicManager()

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
    #: Manage choices in :mod:`~integreat_cms.cms.constants.feedback_ratings`
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
    archived = models.BooleanField(
        default=False,
        verbose_name=_("archived"),
        help_text=_("Whether or not the feedback is archived"),
    )
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="feedback",
        verbose_name=_("marked as read by"),
        help_text=__(
            _("The account that marked this feedback as read."),
            _("If the feedback is unread, this field is empty."),
        ),
    )
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("creation date"),
    )

    @property
    def category(self) -> str:
        """
        This property returns the category (verbose name of the submodel) of this feedback object.

        :return: capitalized category
        """
        return capfirst(self._meta.verbose_name)

    @cached_property
    def rating_sum_positive(self) -> int:
        """
        This property returns the sum of the up-ratings of this object.

        :return: The number of positive ratings on this feedback object
        """
        return self.related_feedback.filter(rating=feedback_ratings.POSITIVE).count()

    @cached_property
    def rating_sum_negative(self) -> int:
        """
        This property returns the sum of the down-ratings of this object.

        :return: The number of negative ratings on this feedback object
        """
        return self.related_feedback.filter(rating=feedback_ratings.NEGATIVE).count()

    @property
    def read(self) -> bool:
        """
        This property returns whether or not the feedback is marked as read or not.
        It is ``True`` if :attr:`~integreat_cms.cms.models.feedback.feedback.Feedback.read_by` is set and ``False``
        otherwise.

        :return: Whether the feedback is marked as read
        """
        return bool(self.read_by)

    @classmethod
    def search(cls, region: Region | None, query: str) -> QuerySet:
        """
        Searches for all feedbacks which match the given `query` in their comment.
        :param region: The current region or None for non-regional feedback
        :param query: The query string used for filtering the events
        :return: A query for all matching objects
        """
        kwargs: dict[str, str | bool | Region | None] = {"comment__icontains": query}
        if region is None:
            kwargs["is_technical"] = True
        else:
            kwargs["is_technical"] = False
            kwargs["region"] = region

        return cls.objects.filter(**kwargs)

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Feedback object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the feedback
        """
        return self.comment

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Feedback: Feedback object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the feedback
        """
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
        default_permissions = ("change", "delete", "view")
