"""
This package contains all views related to places
"""

from __future__ import annotations

from .place_actions import (
    archive_place,
    auto_complete_address,
    copy_place,
    delete_place,
    get_address_from_coordinates,
    restore_place,
    view_place,
)
from .place_form_ajax_view import PlaceFormAjaxView
from .place_form_view import PlaceFormView
from .place_list_view import PlaceListView
from .place_version_view import PlaceVersionView
