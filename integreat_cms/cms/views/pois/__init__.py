"""
This package contains all views related to POIs (points of interest)
"""

from __future__ import annotations

from .poi_actions import (
    archive_poi,
    auto_complete_address,
    delete_poi,
    get_address_from_coordinates,
    restore_poi,
    view_poi,
)
from .poi_form_ajax_view import POIFormAjaxView
from .poi_form_view import POIFormView
from .poi_list_view import POIListView
from .poi_version_view import POIVersionView
