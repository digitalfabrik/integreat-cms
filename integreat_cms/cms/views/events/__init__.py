"""
This package contains all views related to events
"""
from .event_form_view import EventFormView
from .event_list_view import EventListView
from .event_actions import (
    archive,
    restore,
    delete,
    search_poi_ajax,
    duplicate,
)
