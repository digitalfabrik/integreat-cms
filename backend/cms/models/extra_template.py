from django.db import models
from django.contrib.postgres.fields import JSONField


class ExtraTemplate(models.Model):
    name = models.CharField(250)
    alias = models.CharField(60)
    thumbnail = models.CharField(250)
    url = models.CharField(250)
    post_data = JSONField(250)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
