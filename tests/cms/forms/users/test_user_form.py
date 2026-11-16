from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from integreat_cms.cms.forms.users.user_form import UserForm
from integreat_cms.cms.models import User

if TYPE_CHECKING:
    from integreat_cms.cms.models import Role


@pytest.mark.django_db
@pytest.mark.parametrize("existing_user", [False, True], ids=["create", "edit"])
@pytest.mark.parametrize(
    "attribute",
    ["username", "email", "first_name", "last_name", "full_name"],
)
def test_user_form_rejects_submitted_personal_information(
    password_user: User,
    submitted_profile: dict[str, str],
    existing_user: bool,
    attribute: str,
) -> None:
    """Validate submitted attributes, including edits to existing profiles (#4333)."""
    data = submitted_profile.copy()
    data["password"] = (
        data["first_name"] + data["last_name"]
        if attribute == "full_name"
        else data[attribute]
    )
    original_profile = (
        password_user.username,
        password_user.email,
        password_user.first_name,
        password_user.last_name,
        password_user.password,
    )
    form = UserForm(instance=password_user if existing_user else User(), data=data)

    assert not form.is_valid()
    assert form.has_error("password", "password_too_similar")
    assert set(form.errors) == {"password"}
    password_user.refresh_from_db()
    assert (
        password_user.username,
        password_user.email,
        password_user.first_name,
        password_user.last_name,
        password_user.password,
    ) == original_profile
    assert not User.objects.filter(username=data["username"]).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("existing_user", [False, True], ids=["create", "edit"])
def test_user_form_accepts_unrelated_password(
    password_user: User,
    submitted_profile: dict[str, str],
    existing_user: bool,
) -> None:
    """A valid submitted password remains usable for both creation and editing."""
    form = UserForm(
        instance=password_user if existing_user else User(),
        data={**submitted_profile, "password": "Unrelated!Cedar9Moon"},
    )

    assert form.is_valid(), form.errors
    user = form.save()
    user.refresh_from_db()
    assert (user.pk == password_user.pk) == existing_user
    assert user.username == submitted_profile["username"]
    assert user.email == submitted_profile["email"]
    assert user.check_password("Unrelated!Cedar9Moon")


@pytest.mark.django_db
def test_user_form_empty_password_preserves_existing_password(
    password_user: User,
    password_role: Role,
) -> None:
    """Editing a profile without a password must keep the existing hash."""
    original_hash = password_user.password
    form = UserForm(
        instance=password_user,
        data={
            "username": password_user.username,
            "email": password_user.email,
            "role": str(password_role.pk),
            "password": "",
        },
    )

    assert form.is_valid(), form.errors
    form.save()
    password_user.refresh_from_db()
    assert password_user.password == original_hash
