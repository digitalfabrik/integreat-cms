"""
This package contains all views related to POIs (points of interest)
"""
from .poi_form_view import POIFormView
from .poi_actions import (
    view_poi,
    archive_poi,
    restore_poi,
    delete_poi,
)
from .poi_list_view import POIListView
