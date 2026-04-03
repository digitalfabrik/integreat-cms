"""
Shared test constants.

Role identifiers and role groups used across test parametrization.
Extracted from ``conftest.py`` so they can be imported without triggering
fixture registration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from integreat_cms.cms.constants.roles import (
    APP_TEAM,
    AUTHOR,
    CMS_TEAM,
    EDITOR,
    EVENT_MANAGER,
    MANAGEMENT,
    MARKETING_TEAM,
    OBSERVER,
    SERVICE_TEAM,
)

if TYPE_CHECKING:
    from typing import Final


#: A role identifier for superusers
ROOT: Final = "ROOT"
#: A role identifier for anonymous users
ANONYMOUS: Final = "ANONYMOUS"

#: All roles with editing permissions
WRITE_ROLES: Final = [MANAGEMENT, EDITOR, AUTHOR, EVENT_MANAGER]
#: All roles of region users
REGION_ROLES: Final = [*WRITE_ROLES, OBSERVER]
#: All roles of staff users
STAFF_ROLES: Final = [ROOT, SERVICE_TEAM, CMS_TEAM, APP_TEAM, MARKETING_TEAM]
#: All roles of staff users that don't just have read-only permissions
PRIV_STAFF_ROLES: Final = [ROOT, APP_TEAM, SERVICE_TEAM, CMS_TEAM]
#: All roles of staff users that don't just have read-only permissions
HIGH_PRIV_STAFF_ROLES: Final = [ROOT, SERVICE_TEAM, CMS_TEAM]
#: All region and staff roles
ROLES: Final = REGION_ROLES + STAFF_ROLES
#: All region and staff roles and anonymous users
ALL_ROLES: Final = [*ROLES, ANONYMOUS]
