"""
This package contains all views related to feedback
"""
from .admin_feedback_list_view import AdminFeedbackListView
from .region_feedback_list_view import RegionFeedbackListView
from .admin_feedback_actions import (
    mark_admin_feedback_as_read,
    mark_admin_feedback_as_unread,
    delete_admin_feedback,
)
from .region_feedback_actions import (
    mark_region_feedback_as_read,
    mark_region_feedback_as_unread,
    delete_region_feedback,
)
