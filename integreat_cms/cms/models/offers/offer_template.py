from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ...constants import postal_code
from ...utils.translation_utils import gettext_many_lazy as __
from ..abstract_base_model import AbstractBaseModel


class OfferTemplate(AbstractBaseModel):
    """
    The OfferTemplate model is used to store templates of offers which can be activated for specific regions. The
    information stored in an offer template is global, so if you need parameters, which depend on local information
    of a region, it has to be added to the :class:`~integreat_cms.cms.models.regions.region.Region` model.
    """

    name = models.CharField(max_length=250, verbose_name=_("name"))
    slug = models.SlugField(
        max_length=60,
        unique=True,
        verbose_name=_("slug"),
        help_text=__(
            _("String identifier without spaces and special characters."),
            _("Unique per region and language."),
            _("Leave blank to generate unique parameter from name"),
        ),
    )
    thumbnail = models.URLField(
        blank=True, max_length=250, verbose_name=_("thumbnail URL")
    )
    url = models.URLField(
        blank=True,
        max_length=250,
        verbose_name=_("URL"),
        help_text=_("This will be an external API endpoint in most cases."),
    )
    post_data = models.JSONField(
        max_length=250,
        default=dict,
        blank=True,
        verbose_name=_("POST parameter"),
        help_text=__(
            _("Additional POST data for retrieving the URL."), _("Specify as JSON.")
        ),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.postal_code`
    use_postal_code = models.CharField(
        max_length=4,
        choices=postal_code.CHOICES,
        default=postal_code.NONE,
        verbose_name=_("use postal code"),
        help_text=_(
            "Whether and how to insert the postcode of the region into the URL or POST data"
        ),
    )
    supported_by_app_in_content = models.BooleanField(
        default=False,
        blank=True,
        verbose_name=_("supported by app in content"),
        help_text=_(
            "Whether the Integreat app supports displaying offers from this provider in pages"
        ),
    )
    is_zammad_form = models.BooleanField(
        default=False,
        blank=True,
        verbose_name=_("is Zammad form"),
        help_text=_("Whether this offer should be treated as a Zammad form by the App"),
    )
    created_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("creation date"),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``OfferTemplate object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the offer template
        """
        return self.name

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<OfferTemplate: OfferTemplate object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the offer template
        """
        return f"<OfferTemplate (id: {self.id}, slug: {self.slug})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("offer template")
        #: The plural verbose name of the model
        verbose_name_plural = _("offer templates")
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["slug"]
