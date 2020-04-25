from django.db import models


class BedTargetGroup(models.Model):

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True, blank=True, allow_unicode=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = ()
        permissions = (
            ('manage_bed_target_groups', 'Can manage bed target groups'),
        )
