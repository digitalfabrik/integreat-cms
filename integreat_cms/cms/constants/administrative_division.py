"""
This module contains constants which represent all possible administrative divisions of a region in Germany.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: Federal state (German: "Bundesland")
FEDERAL_STATE: Final = "FEDERAL_STATE"
#: Area state (German: "Flächenland")
AREA_STATE: Final = "AREA_STATE"
#: Free state (German: "Freistaat")
FREE_STATE: Final = "FREE_STATE"
#: City state (German: "Stadtstaat")
CITY_STATE: Final = "CITY_STATE"
#: Governmental district (German: "Regierungsbezirk")
GOVERNMENTAL_DISTRICT: Final = "GOVERNMENTAL_DISTRICT"
#: Urban district (German: "Kreisfreie Stadt")
URBAN_DISTRICT: Final = "URBAN_DISTRICT"
#: Rural district (German: "Landkreis")
RURAL_DISTRICT: Final = "RURAL_DISTRICT"
#: District (German: "Kreis")
DISTRICT: Final = "DISTRICT"
#: City (German: "Stadt")
CITY: Final = "CITY"
#: City and district (German: "Stadt und Landkreis")
CITY_AND_DISTRICT: Final = "CITY_AND_DISTRICT"
#: Region (German: "Region")
REGION: Final = "REGION"
#: Municipality (German: "Gemeinde")
MUNICIPALITY: Final = "MUNICIPALITY"
#: Collective municipality (German: "Verbandsgemeinde")
COLLECTIVE_MUNICIPALITY: Final = "COLLECTIVE_MUNICIPALITY"
#: Initial reception center (German: "Erstaufnahmeeinrichtung")
INITIAL_RECEPTION_CENTER: Final = "INITIAL_RECEPTION_CENTER"

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[str, Promise]]] = [
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
]
