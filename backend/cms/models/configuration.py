from django.db import models


class Configuration(models.Model):
    key = models.CharField(max_length=100, unique=True, blank=False)
    value = models.CharField(max_length=1000, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
