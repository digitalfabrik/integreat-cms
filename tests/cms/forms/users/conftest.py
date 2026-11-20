from __future__ import annotations

import pytest
from django.contrib.auth.models import Group

from integreat_cms.cms.constants import roles
from integreat_cms.cms.models import Role, User


@pytest.fixture
def password_user(db: None) -> User:
    """Create a user with distinct attributes for similarity checks."""
    return User.objects.create_user(
        username="copper-orchard",
        email="silverfinch@example.org",
        first_name="Alexandriannabelle",
        last_name="Montgomery",
        password="Original!River7Cloud",  # noqa: S106
    )


@pytest.fixture
def password_role(db: None) -> Role:
    """Provide a non-staff role without loading unrelated content fixtures."""
    return Role.objects.create(
        name=roles.EDITOR,
        group=Group.objects.create(name="Password regression editor"),
        staff_role=False,
    )


@pytest.fixture
def submitted_profile(password_role: Role) -> dict[str, str]:
    """Return fresh form data distinct from the existing user's profile."""
    return {
        "username": "violet-lantern",
        "email": "seabird@example.net",
        "first_name": "Christophersonella",
        "last_name": "Harrington",
        "role": str(password_role.pk),
    }
