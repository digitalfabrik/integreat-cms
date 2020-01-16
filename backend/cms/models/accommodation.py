from django.db import models
from django.conf import settings
from django.utils import timezone

from .language import Language
from .organization import Organization
from .poi import POI
from ..constants import status


class Accommodation(POI):
    """
    A special kind of POI which is used for the cold aid functionality
    """
    institution = models.ForeignKey(Organization, null=False, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=12, null=False)
    mobile_number = models.CharField(max_length=12, null=False)
    wc_available = models.BooleanField(default=False)
    shower_available = models.BooleanField(default=False)
    animals_allowed = models.BooleanField(default=False)
    intoxicated_allowed = models.BooleanField()
    spoken_languages = models.ManyToManyField(Language)
    intake_from = models.TimeField()
    intake_to = models.TimeField()

    class Meta:
        default_permissions = ()
        permissions = (
            ('manage_accommodations', 'can manage accommodations'),
        )


class AccommodationTranslation(models.Model):
    """
    Translation of accommodation fields
    """
    rules_of_accommodation = models.TextField()
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=200, blank=True, allow_unicode=True)
    accommodation = models.ForeignKey(
        Accommodation,
        related_name='translations',
        null=True,
        on_delete=models.SET_NULL
    )
    status = models.CharField(max_length=6, choices=status.CHOICES, default=status.DRAFT)
    short_description = models.CharField(max_length=250)
    description = models.TextField()
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    version = models.PositiveIntegerField(default=0)
    minor_edit = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    @property
    def foreign_object(self):
        return self.accommodation

    @property
    def permalink(self):
        return '/'.join([
            self.accommodation.region.slug,
            self.language.code,
            'accommodations',
            self.slug
        ])

    class Meta:
        default_permissions = ()
