from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class Organization(models.Model):
    """
    Data model representing an organization
    """

    name = models.CharField(max_length=200, verbose_name=_("name"))
    slug = models.SlugField(
        max_length=200,
        unique=True,
        allow_unicode=True,
        verbose_name=_("slug"),
        help_text=_("Unique string identifier without spaces and special characters."),
    )
    icon = models.ImageField(
        null=True,
        blank=True,
        upload_to="organizations/%Y/%m/%d",
        verbose_name=_("logo"),
    )

    created_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("creation date"),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Organization object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the organization
        :rtype: str
        """
        return self.name

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Organization: Organization object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the organization
        :rtype: str
        """
        return f"<Organization (id: {self.id}, slug: {self.slug})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("organization")
        #: The plural verbose name of the model
        verbose_name_plural = _("organizations")
        #: The default permissions for this model
        default_permissions = ()
        #: The custom permissions for this model
        permissions = (("manage_organizations", "Can manage organizations"),)
