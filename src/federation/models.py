from django.db import models
from django.utils import timezone


class CMSCache(models.Model):
    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=False)
    last_contact_attempt_successful = models.BooleanField(default=True)
    last_contact = models.DateTimeField(default=timezone.now)

    @property       #todo: is the usage of this decorator correct?
    def use_regions(self) -> bool:
        return  self.active and self.last_contact_attempt_successful

    def persist_successful_contact_attempt(self):
        self.last_contact = timezone.now()
        self.last_contact_attempt_successful = True
        self.save()

    def persist_failed_contact_attempt(self):
        self.last_contact_attempt_successful = False
        self.save()

class RegionCache(models.Model):
    parentCMS = models.ForeignKey(CMSCache, on_delete=models.CASCADE)
    path = models.CharField(max_length=60)
    postal_code = models.CharField(max_length=10)
    prefix = models.CharField(max_length=100)
    name_without_prefix = models.CharField(max_length=100)
    aliases = models.CharField(max_length=100)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    class Meta:
        unique_together = (("parentCMS", "path"),)


# TODO Discuss: max_length of CharField's (use TextFields?),
# TODO Discuss: unique_together instead of composite primary key
