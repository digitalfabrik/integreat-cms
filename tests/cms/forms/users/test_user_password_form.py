from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from integreat_cms.cms.forms.users.user_password_form import UserPasswordForm

if TYPE_CHECKING:
    from integreat_cms.cms.models import User


@pytest.mark.django_db
@pytest.mark.parametrize(
    "attribute",
    ["username", "email", "first_name", "last_name", "full_name"],
)
def test_password_change_rejects_personal_information(
    password_user: User,
    attribute: str,
) -> None:
    """Reject personal information through the actual password form (#4333)."""
    password = (
        password_user.first_name + password_user.last_name
        if attribute == "full_name"
        else getattr(password_user, attribute)
    )
    original_hash = password_user.password
    form = UserPasswordForm(
        instance=password_user,
        data={
            "old_password": "Original!River7Cloud",
            "new_password": password,
            "new_password_confirm": password,
        },
    )

    assert not form.is_valid()
    assert form.has_error("new_password", "password_too_similar")
    assert set(form.errors) == {"new_password"}
    password_user.refresh_from_db()
    assert password_user.password == original_hash


@pytest.mark.django_db
def test_password_change_accepts_unrelated_password(password_user: User) -> None:
    """Save a valid password while replacing the previous credentials."""
    password = "Unrelated!Cedar9Moon"
    form = UserPasswordForm(
        instance=password_user,
        data={
            "old_password": "Original!River7Cloud",
            "new_password": password,
            "new_password_confirm": password,
        },
    )

    assert form.is_valid(), form.errors
    form.save()
    password_user.refresh_from_db()
    assert password_user.check_password(password)
    assert not password_user.check_password("Original!River7Cloud")


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("password", "error_code"),
    [
        ("Az!7", "password_too_short"),
        ("password", "password_too_common"),
        ("739162840573", "password_entirely_numeric"),
    ],
)
def test_password_change_keeps_strength_validation(
    password_user: User,
    password: str,
    error_code: str,
) -> None:
    """Moving validation into clean() must preserve the other password rules."""
    form = UserPasswordForm(
        instance=password_user,
        data={
            "old_password": "Original!River7Cloud",
            "new_password": password,
            "new_password_confirm": password,
        },
    )

    assert not form.is_valid()
    assert form.has_error("new_password", error_code)


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_field", ["old_password", "new_password_confirm"])
def test_password_change_rejects_incorrect_credentials(
    password_user: User,
    invalid_field: str,
) -> None:
    """A valid new password cannot bypass old-password or confirmation checks."""
    original_hash = password_user.password
    data = {
        "old_password": "Original!River7Cloud",
        "new_password": "Unrelated!Cedar9Moon",
        "new_password_confirm": "Unrelated!Cedar9Moon",
    }
    data[invalid_field] = "Different!Birch8Star"
    form = UserPasswordForm(instance=password_user, data=data)

    assert not form.is_valid()
    assert set(form.errors) == {invalid_field}
    password_user.refresh_from_db()
    assert password_user.password == original_hash


@pytest.mark.parametrize(
    "field", ["old_password", "new_password", "new_password_confirm"]
)
def test_password_change_requires_each_field(password_user: User, field: str) -> None:
    """An omitted password field must produce a field-level validation error."""
    data = {
        "old_password": "Original!River7Cloud",
        "new_password": "Unrelated!Cedar9Moon",
        "new_password_confirm": "Unrelated!Cedar9Moon",
    }
    del data[field]
    form = UserPasswordForm(instance=password_user, data=data)

    assert not form.is_valid()
    assert form.has_error(field, "required")
