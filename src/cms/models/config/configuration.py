from django.db import models
from django.utils.translation import ugettext_lazy as _


class Configuration(models.Model):
    """
    The Configuration model is used for settings which should reside in the database.
    """

    key = models.CharField(
        max_length=100,
        unique=True,
        blank=False,
        verbose_name=_("key"),
    )
    value = models.TextField(blank=False, verbose_name=_("value"))
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("creation date"),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("configuration")
        #: The plural verbose name of the model
        verbose_name_plural = _("configurations")
        #: The default permissions for this model
        default_permissions = ()
        #:  The custom permissions for this model
        permissions = (("manage_configuration", "Can manage configuration"),)
