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
    value = models.CharField(max_length=1000, blank=False, verbose_name=_("value"))
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("creation date"),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Configuration object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the configuration
        :rtype: str
        """
        return f"{self.key}: {self.value}"

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Configuration: Configuration object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the configuration
        :rtype: str
        """
        return f"<Configuration (id: {self.id}, key: {self.key}, value: {self.value})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("configuration")
        #: The plural verbose name of the model
        verbose_name_plural = _("configurations")
        #: The default permissions for this model
        default_permissions = ()
        #:  The custom permissions for this model
        permissions = (("manage_configuration", "Can manage configuration"),)
