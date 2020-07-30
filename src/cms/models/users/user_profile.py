from django.conf import settings
from django.db import models

from .organization import Organization
from ..regions.region import Region


class UserProfile(models.Model):
    """
    Data model representing a user profile

    :param id: The database id of the user profile

    Relationship fields:

    :param user: The user this profile belongs to (related name: ``profile``)
    :param regions: The regions of this user (related name: ``users``)
    :param organization: The organization of the user (related name: ``members``)
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE
    )
    regions = models.ManyToManyField(Region, related_name="users", blank=True)
    organization = models.ForeignKey(
        Organization,
        related_name="members",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    @property
    def roles(self):
        return self.user.groups.all()

    def __str__(self):
        return self.user.username

    class Meta:
        default_permissions = ()
