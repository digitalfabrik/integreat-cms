"""
config for search function in list views
search fields defined here should be of the form
{
  field_name: {"weight": int, "tokenize": bool},
  ...
}

The weight and tokenize attributes are used to attempt to find useful
search suggestions. A greater weight means that matches with this field
will rank higher in the search suggestion list.
The "tokenize" config parameter is True by default. If set to False,
the field values that match the search query will not be split into tokens.
"""

CONTACT_SEARCH_FIELDS = {
    "name": {"weight": 2, "tokenize": False},
    "location__translations__title": {"weight": 2, "tokenize": False},
    "area_of_responsibility": {"weight": 1},
}

EVENT_SEARCH_FIELDS = {
    "title": {"weight": 1, "tokenize": False},
}

LOCATION_SEARCH_FIELDS = {
    "title": {"weight": 1, "tokenize": False},
}

PAGE_SEARCH_FIELDS = {
    "translations__title": {"weight": 1, "tokenize": False},
}