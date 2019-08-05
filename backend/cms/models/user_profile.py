from django.db import models
from django.conf import settings

from .region import Region
from .organization import Organization


class UserProfile(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', on_delete=models.CASCADE)
    regions = models.ManyToManyField(Region, blank=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

    @property
    def roles(self):
        return self.user.groups.all()

    def __str__(self):
        return self.user.username

    class Meta:
        default_permissions = ()
