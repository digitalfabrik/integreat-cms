from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from ..languages.language import Language
from ..users.organization import Organization
from ..pois.poi import POI


class Accommodation(POI):
    """
    A special kind of POI which is used for the cold aid functionality
    """
    institution = models.ForeignKey(Organization, related_name='accommodations', null=False, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=25, blank=True)
    mobile_number = models.CharField(max_length=25, blank=True)
    wc_available = models.BooleanField(default=False)
    shower_available = models.BooleanField(default=False)
    animals_allowed = models.BooleanField(default=False)
    intoxicated_allowed = models.BooleanField(default=False)
    spoken_languages = models.ManyToManyField(Language, related_name='accommodations')
    intake_from = models.TimeField()
    intake_to = models.TimeField()

    objects = models.Manager()

    @property
    def languages(self):
        accommodation_translations = self.accommodation_translations.prefetch_related('language').all()
        languages = []
        for accommodation_translation in accommodation_translations:
            languages.append(accommodation_translation.language)
        return languages

    def get_translation(self, language_code):
        try:
            accommodation_translation = self.accommodation_translations.filter(language__code=language_code).first()
        except ObjectDoesNotExist:
            accommodation_translation = None
        return accommodation_translation

    class Meta:
        default_permissions = ()
        permissions = (
            ('manage_accommodations', 'can manage accommodations'),
        )
