from __future__ import annotations

import json

import pytest
from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone

from integreat_cms.cms.models import ApiToken, Region


def _token_for(username: str) -> str:
    """
    Create an API token for the given user

    :param username: The username of the token's user
    :return: The plaintext token
    """
    user = get_user_model().objects.get(username=username)
    _token, plaintext = ApiToken.create_token(user, f"test-{username}")
    return plaintext


@pytest.mark.django_db
def test_get_region_settings(load_test_data: None) -> None:
    """
    The endpoint returns the writable settings plus the derived budget values.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    endpoint = reverse("api:region_settings", kwargs={"region_slug": "augsburg"})
    response = Client().get(
        endpoint,
        headers={"authorization": f"Bearer {_token_for('root')}"},
    )

    assert response.status_code == 200
    data = response.json()
    for field in (
        "events_enabled",
        "locations_enabled",
        "contacts_enabled",
        "external_news_enabled",
        "integreat_chat_enabled",
        "push_notifications_enabled",
        "mt_budget_booked",
        "mt_renewal_month",
        "mt_budget_adjustment",
    ):
        assert field in data
    assert data["mt_budget"] == data["mt_budget_booked"] + data["mt_budget_adjustment"]


@pytest.mark.django_db
def test_post_updates_settings_and_records_sync(load_test_data: None) -> None:
    """
    A POST writes the supplied fields and marks the region as API-managed.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    region = Region.objects.get(slug="augsburg")
    assert region.api_settings_synced_at is None

    endpoint = reverse("api:region_settings", kwargs={"region_slug": "augsburg"})
    response = Client().post(
        endpoint,
        data=json.dumps(
            {
                "events_enabled": False,
                "mt_budget_booked": 123456,
                "mt_budget_adjustment": -6456,
            },
        ),
        content_type="application/json",
        headers={"authorization": f"Bearer {_token_for('root')}"},
    )

    assert response.status_code == 200
    region.refresh_from_db()
    assert region.events_enabled is False
    assert region.mt_budget_booked == 123456
    assert region.mt_budget_adjustment == -6456
    # The adjustment is added on top of the booked budget
    assert region.mt_budget == 117000
    assert region.api_settings_synced_at is not None
    assert region.is_api_managed


@pytest.mark.django_db
def test_post_accepts_budget_outside_the_predefined_sizes(load_test_data: None) -> None:
    """
    The model no longer restricts the budget to the package sizes, so any integer is accepted.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    endpoint = reverse("api:region_settings", kwargs={"region_slug": "augsburg"})
    response = Client().post(
        endpoint,
        data=json.dumps({"mt_budget_booked": 77777}),
        content_type="application/json",
        headers={"authorization": f"Bearer {_token_for('root')}"},
    )

    assert response.status_code == 200
    assert Region.objects.get(slug="augsburg").mt_budget_booked == 77777


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload",
    [
        # Core fields must not be writable
        {"slug": "hacked"},
        {"name": "Hacked"},
        # Unknown field
        {"does_not_exist": 1},
        # Read-only derived value
        {"mt_budget_used": 0},
    ],
)
def test_post_rejects_non_writable_fields(
    load_test_data: None,
    payload: dict,
) -> None:
    """
    Only the allow-listed settings may be written.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param payload: The rejected request body
    """
    endpoint = reverse("api:region_settings", kwargs={"region_slug": "augsburg"})
    response = Client().post(
        endpoint,
        data=json.dumps(payload),
        content_type="application/json",
        headers={"authorization": f"Bearer {_token_for('root')}"},
    )

    assert response.status_code == 400
    region = Region.objects.get(slug="augsburg")
    assert region.slug == "augsburg"
    assert region.api_settings_synced_at is None


@pytest.mark.django_db
def test_post_rejects_invalid_values(load_test_data: None) -> None:
    """
    Values which do not pass the model validation are rejected with 400.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    endpoint = reverse("api:region_settings", kwargs={"region_slug": "augsburg"})
    token = _token_for("root")

    # Renewal month outside the valid choices
    response = Client().post(
        endpoint,
        data=json.dumps({"mt_renewal_month": 42}),
        content_type="application/json",
        headers={"authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400

    # Non-integer budget
    response = Client().post(
        endpoint,
        data=json.dumps({"mt_budget_booked": "many words"}),
        content_type="application/json",
        headers={"authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400

    assert Region.objects.get(slug="augsburg").api_settings_synced_at is None


@pytest.mark.django_db
def test_requires_authentication(load_test_data: None) -> None:
    """
    Without a valid token the endpoint answers with 403.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    endpoint = reverse("api:region_settings", kwargs={"region_slug": "augsburg"})

    assert Client().get(endpoint).status_code == 403
    assert (
        Client()
        .get(endpoint, headers={"authorization": "Bearer nope.nope"})
        .status_code
        == 403
    )


@pytest.mark.django_db
def test_requires_permission(load_test_data: None) -> None:
    """
    A token of a user without ``cms.change_region`` is rejected.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    unprivileged = get_user_model().objects.filter(is_superuser=False).first()
    _token, plaintext = ApiToken.create_token(unprivileged, "test-unprivileged")

    endpoint = reverse("api:region_settings", kwargs={"region_slug": "augsburg"})
    response = Client().get(
        endpoint,
        headers={"authorization": f"Bearer {plaintext}"},
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_unknown_region_returns_404(load_test_data: None) -> None:
    """
    An unknown region slug results in a 404.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    endpoint = reverse("api:region_settings", kwargs={"region_slug": "does-not-exist"})
    response = Client().get(
        endpoint,
        headers={"authorization": f"Bearer {_token_for('root')}"},
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_api_managed_region_form_shows_the_real_budget(load_test_data: None) -> None:
    """
    An API-managed region may have a budget outside the predefined package sizes, so the form
    must not fall back to a dropdown which would display a wrong value.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    from integreat_cms.cms.forms import RegionForm

    region = Region.objects.get(slug="augsburg")
    region.mt_budget_booked = 77777
    region.api_settings_synced_at = timezone.now()
    region.save()

    form = RegionForm(instance=region)

    assert form["mt_budget_booked"].value() == 77777
    assert form.fields["mt_budget_booked"].disabled
    # A choice field would silently render the first option instead of the actual value
    assert not hasattr(form.fields["mt_budget_booked"], "choices")
