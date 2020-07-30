from django.db import models


class Configuration(models.Model):
    """
    The Configuration model is used for settings which should reside in the database.

    :param id: The database id of the configuration
    :param key: The key of the configuration
    :param value: The value of the configuration
    :param created_date: The date and time when the configuration was created
    :param last_updated: The date and time when the configuration was last changed
    """

    key = models.CharField(max_length=100, unique=True, blank=False)
    value = models.CharField(max_length=1000, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = ()
        permissions = (("manage_configuration", "Can manage configuration"),)
