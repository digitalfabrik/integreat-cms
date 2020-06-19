from django.db import models
from django.utils import timezone


class Organization(models.Model):
    """
    Data model representing an organization

    :param id: The database id of the organization
    :param name: The name of the organization
    :param slug: The slug of the organization
    :param thumbnail: The url to the thumbnail image of the organization
    :param created_date: The date and time when the organization was created
    :param last_updated: The date and time when the organization was last updated

    Reverse relationships:

    :param members: All users who are members of the organization
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, allow_unicode=True)
    thumbnail = models.CharField(max_length=250, blank=True)

    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = ()
        permissions = (
            ('manage_organizations', 'Can manage organizations'),
        )
