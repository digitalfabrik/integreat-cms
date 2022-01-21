"""
This package contains all views related to users
"""
from .user_list_view import UserListView
from .user_form_view import UserFormView
from .user_actions import delete_user, resend_activation_link
from .region_user_list_view import RegionUserListView
from .region_user_form_view import RegionUserFormView
from .region_user_actions import delete_region_user, resend_activation_link_region
