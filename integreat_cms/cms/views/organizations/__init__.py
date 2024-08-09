"""
This package contains all views related to organizations
"""

from __future__ import annotations

from .organization_actions import archive, delete, restore
from .organization_form_view import OrganizationFormView
from .organization_list_view import OrganizationListView
