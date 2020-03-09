"""
This module contains constants which represent all possible administrative divisions of a region in Germany:

* ``CITY``: City (German: "Stadt")

* ``DISTRICT``: District (German: "Kreis")

* ``RURAL_DISTRICT``: Rural district (German: "Landkreis")

* ``REGION``: Region (German: "Region")

* ``CITY_AND_DISTRICT``: City and district (German: "Stadt und Landkreis")

* ``URBAN_DISTRICT``: Urban district (German: "Kreisfreie Stadt")

* ``GOVERNMENTAL_DISTRICT``: Governmental district (German: "Regierungsbezirk")

* ``CITY_STATE``: City state (German: "Stadtstaat")

* ``AREA_STATE``: Area state (German: "Flächenland")

* ``FREE_STATE``: Free state (German: "Freistaat")

* ``FEDERAL_STATE``: Federal state (German: "Bundesland")

* ``MUNICIPALITY``: Municipality (German: "Gemeinde")

* ``COLLECTIVE_MUNICIPALITY``: Collective municipality (German: "Gemeindeverband")

* ``INITIAL_RECEPTION_CENTER``: Initial reception center (German: "Erstaufnahmeeinrichtung")
"""

from django.utils.translation import ugettext_lazy as _


FEDERAL_STATE = 'FEDERAL_STATE'
AREA_STATE = 'AREA_STATE'
FREE_STATE = 'FREE_STATE'
CITY_STATE = 'CITY_STATE'
GOVERNMENTAL_DISTRICT = 'GOVERNMENTAL_DISTRICT'
URBAN_DISTRICT = 'URBAN_DISTRICT'
RURAL_DISTRICT = 'RURAL_DISTRICT'
DISTRICT = 'DISTRICT'
CITY = 'CITY'
CITY_AND_DISTRICT = 'CITY_AND_DISTRICT'
REGION = 'REGION'
MUNICIPALITY = 'MUNICIPALITY'
COLLECTIVE_MUNICIPALITY = 'COLLECTIVE_MUNICIPALITY'
INITIAL_RECEPTION_CENTER = 'INITIAL_RECEPTION_CENTER'

CHOICES = (
    (CITY, _('City')),
    (DISTRICT, _('District')),
    (RURAL_DISTRICT, _('Rural district')),
    (REGION, _('Region')),
    (CITY_AND_DISTRICT, _('City and district')),
    (URBAN_DISTRICT, _('Urban district')),
    (GOVERNMENTAL_DISTRICT, _('Governmental district')),
    (CITY_STATE, _('City state')),
    (AREA_STATE, _('Area state')),
    (FREE_STATE, _('Free state')),
    (FEDERAL_STATE, _('Federal state')),
    (MUNICIPALITY, _('Municipality')),
    (COLLECTIVE_MUNICIPALITY, _('Collective municipality')),
    (INITIAL_RECEPTION_CENTER, _('Initial reception center')),
)
