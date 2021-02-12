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
    thumbnail = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_("thumbnail image"),
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
        This overwrites the default Python __str__ method which would return <Organization object at 0xDEADBEEF>

        :return: The string representation (in this case the title) of the organization
        :rtype: str
        """
        return self.name

    class Meta:
        #: The verbose name of the model
        verbose_name = _("organization")
        #: The plural verbose name of the model
        verbose_name_plural = _("organizations")
        #: The default permissions for this model
        default_permissions = ()
        #: The custom permissions for this model
        permissions = (("manage_organizations", "Can manage organizations"),)
