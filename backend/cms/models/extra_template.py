from django.db import models
from django.contrib.postgres.fields import JSONField


class ExtraTemplate(models.Model):
    name = models.CharField(max_length=250)
    alias = models.CharField(max_length=60)
    thumbnail = models.CharField(max_length=250)
    url = models.CharField(max_length=250)
    post_data = JSONField(max_length=250, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
