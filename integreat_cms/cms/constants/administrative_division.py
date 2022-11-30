"""
This module contains constants which represent all possible administrative divisions of a region in Germany.
"""
from django.utils.translation import gettext_lazy as _


#: Federal state (German: "Bundesland")
FEDERAL_STATE = "FEDERAL_STATE"
#: Area state (German: "Flächenland")
AREA_STATE = "AREA_STATE"
#: Free state (German: "Freistaat")
FREE_STATE = "FREE_STATE"
#: City state (German: "Stadtstaat")
CITY_STATE = "CITY_STATE"
#: Governmental district (German: "Regierungsbezirk")
GOVERNMENTAL_DISTRICT = "GOVERNMENTAL_DISTRICT"
#: Urban district (German: "Kreisfreie Stadt")
URBAN_DISTRICT = "URBAN_DISTRICT"
#: Rural district (German: "Landkreis")
RURAL_DISTRICT = "RURAL_DISTRICT"
#: District (German: "Kreis")
DISTRICT = "DISTRICT"
#: City (German: "Stadt")
CITY = "CITY"
#: City and district (German: "Stadt und Landkreis")
CITY_AND_DISTRICT = "CITY_AND_DISTRICT"
#: Region (German: "Region")
REGION = "REGION"
#: Municipality (German: "Gemeinde")
MUNICIPALITY = "MUNICIPALITY"
#: Collective municipality (German: "Verbandsgemeinde")
COLLECTIVE_MUNICIPALITY = "COLLECTIVE_MUNICIPALITY"
#: Initial reception center (German: "Erstaufnahmeeinrichtung")
INITIAL_RECEPTION_CENTER = "INITIAL_RECEPTION_CENTER"

#: Choices to use these constants in a database field
CHOICES = (
    (CITY, _("City")),
    (DISTRICT, _("District")),
    (RURAL_DISTRICT, _("Rural district")),
    (REGION, _("Region")),
    (CITY_AND_DISTRICT, _("City and district")),
    (URBAN_DISTRICT, _("Urban district")),
    (GOVERNMENTAL_DISTRICT, _("Governmental district")),
    (CITY_STATE, _("City state")),
    (AREA_STATE, _("Area state")),
    (FREE_STATE, _("Free state")),
    (FEDERAL_STATE, _("Federal state")),
    (MUNICIPALITY, _("Municipality")),
    (COLLECTIVE_MUNICIPALITY, _("Collective municipality")),
    (INITIAL_RECEPTION_CENTER, _("Initial reception center")),
)
