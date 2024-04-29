import os
import re

import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import reverse
from freezegun import freeze_time

from tests.conftest import (
    ANONYMOUS,
    AUTHOR,
    EDITOR,
    EVENT_MANAGER,
    MANAGEMENT,
    MARKETING_TEAM,
    OBSERVER,
    PRIV_STAFF_ROLES,
    STAFF_ROLES,
)


@pytest.mark.django_db
def test_permission_to_view_chat(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:

    client, role = login_role_user

    get_dashboard = reverse(
        "dashboard",
        kwargs={"region_slug": "augsburg"},
    )

    response = client.get(get_dashboard)
    current_dir = os.path.dirname(os.path.abspath(__file__))

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={get_dashboard}"
        )
        return

    with open(current_dir + "/expected_output/chat.html") as file:
        chat_head = file.read()

    if role in [OBSERVER, EVENT_MANAGER, AUTHOR, EDITOR]:
        assert response.status_code == 200
        assert chat_head not in response.content.decode("utf-8")

    elif role in STAFF_ROLES + [MANAGEMENT]:
        assert response.status_code == 200
        assert chat_head in response.content.decode("utf-8")


@pytest.mark.django_db
def test_permission_to_view_news(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user

    dashboard = reverse(
        "dashboard",
        kwargs={"region_slug": "augsburg"},
    )

    response = client.get(dashboard)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={dashboard}"
        )

    else:
        assert response.status_code == 200
        assert "Integreat Neuigkeiten" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_permission_to_view_to_do_board(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user

    dashboard = reverse(
        "dashboard",
        kwargs={"region_slug": "augsburg"},
    )

    response = client.get(dashboard)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={dashboard}"
        )

    elif role in [EVENT_MANAGER, MARKETING_TEAM, OBSERVER]:
        assert response.status_code == 200
        assert "To-Dos" not in response.content.decode("utf-8")
        assert (
            "Hier finden Sie jeden Tag eine Liste mit Vorschlägen, wie Sie die Inhalte auf Ihren Seiten verbessern können."
            not in response.content.decode("utf-8")
        )

    elif role in [PRIV_STAFF_ROLES] + [AUTHOR, EDITOR, MANAGEMENT]:
        assert response.status_code == 200
        assert "To-Dos" in response.content.decode("utf-8")
        assert (
            "Hier finden Sie jeden Tag eine Liste mit Vorschlägen, wie Sie die Inhalte auf Ihren Seiten verbessern können."
            in response.content.decode("utf-8")
        )


@pytest.mark.django_db
def test_permission_to_view_admin_dashboard(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user

    admin_dashboard = reverse("admin_dashboard")

    response = client.get(admin_dashboard)

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={admin_dashboard}"
        )

    elif role not in STAFF_ROLES and not ANONYMOUS:
        assert response.status_code == 403

    elif role in STAFF_ROLES:
        assert response.status_code == 200


@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR], indirect=True
)
@pytest.mark.django_db
@freeze_time("2024-01-01")
def test_number_of_outdated_pages_is_correct(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    expected_number_of_pages = 10

    pages = reverse(
        "pages",
        kwargs={"region_slug": "augsburg", "language_slug": "de"},
    )

    dashboard = reverse(
        "dashboard",
        kwargs={"region_slug": "augsburg"},
    )

    response = client.get(dashboard)

    assert response.status_code == 200
    match = re.search(
        rf'<a href="{pages}\?(|[^"]+&)exclude_pages_without_content=on(|&[^"]+)"[^<>]*>Veraltete Seiten</a>\s*<span>\(Insgesamt ([0-9]+)\)</span>',
        response.content.decode("utf-8"),
    )
    assert match, "Number of outdated pages not displayed"
    assert (
        int(match.group(3)) == expected_number_of_pages
    ), "Wrong number of pages displayed as outdated"


@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR], indirect=True
)
@pytest.mark.django_db
@freeze_time("2024-01-01")
def test_most_outdated_page_is_correct(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    days_since_page_is_outdated = 1602

    dashboard = reverse(
        "dashboard",
        kwargs={"region_slug": "augsburg"},
    )

    response = client.get(dashboard)

    assert response.status_code == 200
    match = re.search(
        r"Die Seite <b>Willkommen</b> wurde seit ([0-9]+) Tagen nicht mehr aktualisiert\.",
        response.content.decode("utf-8"),
    )
    assert match, "Not updated message missing"
    assert (
        int(match.group(1)) == days_since_page_is_outdated
    ), "Not updated message displaying wrong days count"


@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR], indirect=True
)
@pytest.mark.django_db
def test_link_to_most_outdated_page_is_valid(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, _ = login_role_user
    current_dir = os.path.dirname(os.path.abspath(__file__))

    with open(current_dir + "/expected_output/go-to-most-outdated-button.html") as file:
        expected_button = file.read()

    dashboard = reverse(
        "dashboard",
        kwargs={"region_slug": "augsburg"},
    )

    response = client.get(dashboard)

    assert expected_button in response.content.decode("utf-8")
    assert_button_leads_to_valid_page(client)


def assert_button_leads_to_valid_page(client: Client) -> None:
    target_page = reverse(
        "edit_page",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "page_id": 1},
    )
    response = client.get(target_page)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR], indirect=True
)
@pytest.mark.django_db
def test_number_of_drafted_pages_is_correct(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    expected_number_of_pages = 1

    pages = reverse(
        "pages",
        kwargs={"region_slug": "augsburg", "language_slug": "de"},
    )

    dashboard = reverse(
        "dashboard",
        kwargs={"region_slug": "augsburg"},
    )

    response = client.get(dashboard)

    assert response.status_code == 200
    match = re.search(
        rf'<a href="{pages}\?(|[^"]+&)status=DRAFT(|&[^"]+)"[^<>]*>Seiten im Entwurf</a>\s*<span>\(Insgesamt ([0-9]+)\)</span>',
        response.content.decode("utf-8"),
    )
    assert match, "Number of drafted pages not displayed"
    assert (
        int(match.group(3)) == expected_number_of_pages
    ), "Wrong number of pages displayed as outdated"


@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR], indirect=True
)
@pytest.mark.django_db
def test_single_drafted_page_is_correct(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user

    dashboard = reverse(
        "dashboard",
        kwargs={"region_slug": "augsburg"},
    )

    response = client.get(dashboard)

    assert response.status_code == 200
    match = re.search(
        r"Die Seite <b>Über die App Integreat Augsburg</b> liegt nur im Entwurf vor.",
        response.content.decode("utf-8"),
    )
    assert match, "Not updated message missing"
