"""
Configuration for search suggestions in list views.

Search fields should be defined as a dict mapping field names to configuration:

    {
        "field_name": {"weight": int, "tokenize": bool},
        ...
    }

Configuration options:
    - ``weight``: Controls ranking in search suggestions. Higher values rank matches
      higher in the suggestion list. Default: 1
    - ``tokenize``: Whether to split field values into individual tokens. Set to False
      to keep values intact (e.g., for names). Default: True
"""

from __future__ import annotations

CONTACT_SEARCH_FIELDS: dict = {
    "name": {"weight": 2, "tokenize": False},
    "location__translations__title": {"weight": 2, "tokenize": False},
    "area_of_responsibility": {"weight": 1},
}

EVENT_SEARCH_FIELDS: dict = {
    "title": {"weight": 1, "tokenize": False},
}

LOCATION_SEARCH_FIELDS: dict = {
    "title": {"weight": 1, "tokenize": False},
}

PAGE_SEARCH_FIELDS: dict = {
    "translations__title": {"weight": 1, "tokenize": False},
}
