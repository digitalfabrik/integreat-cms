"""
This module contains the region settings which can be written through the API

The list is the single source of truth for both the API endpoint and the region form: the endpoint
only accepts these fields, and the form renders exactly these fields read-only once a region is
managed externally. Core fields such as the name or the slug are deliberately not included — they
identify the region and must never be changed by an external system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final

#: The region settings which an external system may write via the API
WRITABLE_FIELDS: Final[list[str]] = [
    "events_enabled",
    "places_enabled",
    "contacts_enabled",
    "external_news_enabled",
    "integreat_chat_enabled",
    "push_notifications_enabled",
    "mt_budget_booked",
    "mt_renewal_month",
    "mt_budget_adjustment",
]

#: Former names of writable fields which the API still accepts, mapped to their current name.
#: ``locations_enabled`` was renamed with the switch from "POI" to "place" (#4547); external systems
#: such as the CRM keep sending the old name until they are updated, and rejecting it would fail
#: the whole request rather than just this one setting.
DEPRECATED_ALIASES: Final[dict[str, str]] = {
    "locations_enabled": "places_enabled",
}
