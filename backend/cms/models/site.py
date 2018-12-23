from django.db import models


class Site(models.Model):
    STATUS = (
        ('publ', 'Public'),
        ('priv', 'Private'),
        ('arch', 'Archived'),
    )
    name = models.CharField(max_length=250)
    slug = models.CharField(max_length=60)
    status = models.CharField(max_length=4, choices=STATUS)
    pub_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
