from django.db import models

from ..languages.language import Language
from ..users.organization import Organization
from ..pois.poi import POI


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
