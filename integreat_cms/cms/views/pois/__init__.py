"""
This package contains all views related to POIs (points of interest)
"""
from .poi_form_view import POIFormView
from .poi_actions import (
    view_poi,
    archive_poi,
    restore_poi,
    delete_poi,
    auto_complete_address,
    get_address_from_coordinates,
)
from .poi_list_view import POIListView
