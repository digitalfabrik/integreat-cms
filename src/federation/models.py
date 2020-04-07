from django.db import models


class CMSCache(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=50)
    domain = models.CharField(max_length=50)
    public_key = models.CharField(max_length=450)
    confirmed = models.BooleanField(default=False)  # the user manually confirmed the id
    use_regions = models.BooleanField(default=False)
    last_contact = models.DateTimeField()


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
