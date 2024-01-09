import re
from typing import TYPE_CHECKING

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import resolve, reverse

from integreat_cms.cms.models.pages.page_translation import PageTranslation
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

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture

    # TODO: Test
    """
    - Seite ohne Änderung, die automatisch gespeichert wurde, bekommt Nachricht, dass das Autosave übersprungen wurde CHECK?
    - Für den Fall, dass eine manuelle Speicherung keine Änderung hat, teste "messages.info(request, _("No changes detected, but date refreshed"))"
    """


@pytest.mark.django_db
def test_explicitly_archived_page_form_shows_cannot_edit_message(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    # Request page form for archived page
    get_archived_page_form = reverse(
        "edit_page",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "page_id": 24},
    )
    response = client.get(get_archived_page_form)

    if role == EVENT_MANAGER:
        assert response.status_code == 403

    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={get_archived_page_form}"
        )
    else:
        assert response.status_code == 200
        assert (
            "Sie können diese Seite nicht bearbeiten, weil sie archiviert ist."
            in response.content.decode("utf-8")
        )


@pytest.mark.django_db
def test_implicitly_archived_page_form_shows_cannot_edit_message(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    # Request page form for archived page
    get_archived_page_form = reverse(
        "edit_page",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "page_id": 25},
    )
    response = client.get(get_archived_page_form)

    if role == EVENT_MANAGER:
        assert response.status_code == 403

    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={get_archived_page_form}"
        )
    else:
        assert response.status_code == 200
        assert (
            "Sie können diese Seite nicht bearbeiten, weil eine ihrer übergeordneten Seiten archiviert ist, und sie dadurch ebenfalls archiviert ist."
            in response.content.decode("utf-8")
        )


@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR], indirect=True
)
@pytest.mark.django_db
def test_auto_save_page_shows_auto_save_message(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    # Request an auto saved page
    get_auto_saved_page = reverse(
        "edit_page",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "page_id": 15},
    )
    response = client.get(get_auto_saved_page)

    if role == AUTHOR:
        with open("output-autosave.html", "w") as file:
            file.write(response.content.decode("utf-8"))

    assert response.status_code == 200
    if role == AUTHOR:
        assert (
            "Die letzten Änderungen wurden automatisch gespeichert."
            in response.content.decode("utf-8")
        )
    else:
        assert (
            "Die letzten Änderungen wurden automatisch gespeichert. Sie können diese Änderungen in der <a href='/augsburg/pages/de/15/versions/' class='underline hover:no-underline'>Versionsübersicht</a> verwerfen."
            in response.content.decode("utf-8")
        )


@pytest.mark.django_db
def test_review_awaiting_page_shows_pending_review_message(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    # Request an auto saved page
    get_review_pending_page = reverse(
        "edit_page",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "page_id": 14},
    )
    response = client.get(get_review_pending_page)

    if role == EVENT_MANAGER:
        assert response.status_code == 403

    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={get_review_pending_page}"
        )

    else:
        assert response.status_code == 200
        assert (
            "Die letzten Änderungen stehen zur Freigabe aus."
            in response.content.decode("utf-8")
        )

@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR], indirect=True
)
@pytest.mark.django_db
def test_page_without_changes_shows_according_message(
    load_test_data: None,
    login_role_user: tuple[Client, str],
):
    # Log the user in
    client, role = login_role_user

    new_page_url = reverse(
        "new_page",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )

    response = client.post(
        new_page_url,
        data={
            "status": "DRAFT",
            "content": "<p>Seite, die keine Änderungen enthält</p>",
            "title": "Seite, die keine Änderungen enthält",
            "slug": "seite-die-keine-änderungen-enthält",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": True,
        },
    )

    assert response.status_code == 302
    page_edit_url = response.headers.get("location")

    response = client.post(
        page_edit_url,
        data={
            "status": "DRAFT",
            "content": "<p>Seite, die keine Änderungen enthält</p>",
            "title": "Seite, die keine Änderungen enthält",
            "slug": "seite-die-keine-änderungen-enthält",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
        },
    )


    assert response.status_code == 302

    response = client.get(page_edit_url)
    assert response.status_code == 200
    assert (
        "Keine Änderungen vorgenommen, aber Datum aktualisiert"
        in response.content.decode("utf-8")
    )


@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.django_db
def test_first_version_is_not_minor_edit(
    login_role_user: tuple[Client, str],
):
    # Log the user in
    client, role = login_role_user

    # Url to create a new page
    new_page_url = reverse(
        "new_page",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )

    response = client.post(
        new_page_url,
        data={
            "status": "PUBLIC",
            "content": "<p>Seite, die eine geringfügige Änderung sein möchte</p>",
            "title": "Seite, die eine geringfügige Änderungen sein möchte",
            "slug": "seite-die-eine-geringfügige-änderung-sein-möchte",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": True,
        },
    )

    assert response.status_code == 302

    url = response.headers.get("location")
    page_id = resolve(url).kwargs["page_id"]

    page_translations = list(PageTranslation.objects.filter(page__id=page_id))
    assert len(page_translations) == 1
    assert page_translations[0].minor_edit == False

    response = client.get(response.headers.get("location"))
    assert response.status_code == 200
    assert (
        "Die &quot;geringfügige Änderung&quot;-Option wurde deaktiviert, da die erste Version niemals eine geringfügige Änderung sein kann."
        in response.content.decode("utf-8")
    )


@pytest.mark.parametrize(
    "login_role_user",
    STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR, OBSERVER],
    indirect=True,
)
@pytest.mark.django_db
def test_api_token_is_deleted_for_non_experts(
    login_role_user: tuple[Client, str],
):
    client, role = login_role_user

    user = get_user_model().objects.get(username=role.lower())
    verify_expert_user_see_api_token(user, client)
    verify_non_expert_user_do_not_see_api_token(user, client)


def verify_expert_user_see_api_token(user, client):
    user.expert_mode = True
    user.save()
    response = request_arbitrary_page(client)
    assert '<input type="text" name="api_token"' in response.content.decode("utf-8")


def verify_non_expert_user_do_not_see_api_token(user, client):
    user.expert_mode = False
    user.save()
    response = request_arbitrary_page(client)
    assert '<input type="text" name="api_token"' not in response.content.decode("utf-8")


def request_arbitrary_page(client):
    arbitrary_page = reverse(
        "edit_page",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
            "page_id": 1,
        },
    )

    return client.get(arbitrary_page)


@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.django_db
def test_discard_hint_on_autosave(
    login_role_user: tuple[Client, str],
):
    client, role = login_role_user

    # Url to create a new page
    new_page_url = reverse(
        "new_page",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )

    response = client.post(
        new_page_url,
        data={
            "status": "PUBLIC",
            "content": "<p>Seite, die automatisch gespeichert wird</p>",
            "title": "Seite, die automatisch gespeichert wird",
            "slug": "seite-die-automatisch-gespeichert-wird",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": False,
        },
    )

    assert response.status_code == 302
    page_edit_url = response.headers.get("location")

    response = client.post(
        page_edit_url,
        data={
            "status": "AUTO_SAVE",
            "content": "<p>Seite, die automatisch gespeichert wurde</p>",
            "title": "Seite, die automatisch gespeichert wurde",
            "slug": "seite-die-automatisch-gespeichert-wurde",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": False,
        },
    )

    assert response.status_code == 302
    assert response.headers.get("location") == page_edit_url

    response = client.get(page_edit_url)

    assert response.status_code == 200
    assert re.search(
        "Sie können diese Änderungen in der <a [^<>]*>Versionsübersicht</a> verwerfen.",
        response.content.decode("utf-8"),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
def test_reject_hint_on_review(
    login_role_user: tuple[Client, str],
):
    client, _role = login_role_user

    # Url to create a new page
    new_page_url = reverse(
        "new_page",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )

    response = client.post(
        new_page_url,
        data={
            "status": "PUBLIC",
            "content": "<p>Seite, die zur Review vorgelegt wird</p>",
            "title": "Seite, die zur Review vorgelegt wird",
            "slug": "seite-die-zur-review-vorgelegt-wird",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": False,
        },
    )

    assert response.status_code == 302
    page_edit_url = response.headers.get("location")

    response = client.post(
        page_edit_url,
        data={
            "status": "REVIEW",
            "content": "<p>Seite, die zur Review vorgelegt wurde</p>",
            "title": "Seite, die zur Review vorgelegt wurde",
            "slug": "seite-die-zur-review-vorgelegt-wurde",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": False,
        },
    )

    assert response.status_code == 302
    assert response.headers.get("location") == page_edit_url

    response = client.get(page_edit_url)

    assert response.status_code == 200
    assert re.search(
        "Sie können diese Änderungen in der <a [^<>]*>Versionsübersicht</a> ablehnen.",
        response.content.decode("utf-8"),
    )


@pytest.mark.skip(
    reason="Wait until issue #2703 (https://github.com/digitalfabrik/integreat-cms/issues/2703) is resolved"
)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
def test_last_changes_only_saved_as_draft_message(
    login_role_user: tuple[Client, str],
):
    client, _role = login_role_user

    # Url to create a new page
    new_page_url = reverse(
        "new_page",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )

    response = client.post(
        new_page_url,
        data={
            "status": "PUBLIC",
            "content": "<p>Seite, die öffentlich ist</p>",
            "title": "Seite,  die öffentlich ist",
            "slug": "seite-die-öffentlich-ist",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": False,
        },
    )

    assert response.status_code == 302
    page_edit_url = response.headers.get("location")

    response = client.post(
        page_edit_url,
        data={
            "status": "DRAFT",
            "content": "<p>Seite, die manuell als Entwurf gespeichert wird</p>",
            "title": "Seite, die manuell als Entwurf gespeichert wird",
            "slug": "seite-die-manuell-als-entwurf-gespeichert-wurde",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": False,
        },
    )

    assert response.status_code == 302
    assert response.headers.get("location") == page_edit_url

    response = client.get(page_edit_url)

    assert response.status_code == 200
    assert (
        "Die letzten Änderungen wurden nur als Entwurf gespeichert."
        in response.content.decode("utf-8")
    )
    assert re.search(
        "Aktuell wird <a [^<>]*>Version [0-9]+</a> dieser Seite in der App angezeigt\\.",
        response.content.decode("utf-8"),
    )


@pytest.mark.skip(
    # TODO: Entferne das Skip wieder vor dem Push
    reason="We think we discovered a bug, huh?"
)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
def test_hint_autosave_skipped_after_unchanged_autosave(
    login_role_user: tuple[Client, str],
):
    client, _role = login_role_user

    # Url to create a new page
    new_page_url = reverse(
        "new_page",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )

    response = client.post(
        new_page_url,
        data={
            "status": "PUBLIC",
            "content": "<p>Seite, die einen Autosave mit gleichem Inhalt hat</p>",
            "title": "Seite, die einen Autosave mit gleichem Inhalt hat",
            "slug": "seite-die-einen-autosave-mit-gleichem-Inhalt-hat",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": False,
        },
    )

    assert response.status_code == 302
    page_edit_url = response.headers.get("location")

    response = client.post(
        page_edit_url,
        data={
            "status": "AUTO_SAVE",
            "content": "<p>Seite, die einen Autosave mit gleichem Inhalt hat</p>",
            "title": "Seite, die einen Autosave mit gleichem Inhalt hat",
            "slug": "seite-die-einen-autosave-mit-gleichem-Inhalt-hat",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": False,
        },
    )

    assert response.status_code == 200
    assert (
        "Keine Änderungen vorgenommen, automatisches Speichern übersprungen"
        in response.content.decode("utf-8")
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
def test_rename_to_unique_slug_message(
    login_role_user: tuple[Client, str],
):
    client, _role = login_role_user

    page_welcome = next(
        iter(PageTranslation.objects.filter(slug="willkommen").order_by("-version"))
    )
    assert page_welcome is not None

    new_page_url = reverse(
        "new_page",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )

    response = client.post(
        new_page_url,
        data={
            "status": "PUBLIC",
            "content": "<p>Seite, die den Slug Willkommen nicht behalten soll</p>",
            "title": "Seite, die den Slug Willkommen nicht behalten soll",
            "slug": "willkommen",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": False,
        },
    )

    assert response.status_code == 302
    page_edit_url = response.headers.get("location")

    response = client.get(page_edit_url)

    assert response.status_code == 200

    match = re.search(
        "Der URL-Parameter wurde von &#x27;willkommen&#x27; zu &#x27;(.+)&#x27; geändert, da &#x27;willkommen&#x27; bereits von <a [^<>]*>[^<>]+</a> verwendet wird\\.",
        response.content.decode("utf-8"),
    )

    assert match is not None
    assert match.group(1) != "willkommen"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
def test_review_message(
    login_role_user: tuple[Client, str],
):
    client, _role = login_role_user

    new_page_url = reverse(
        "new_page",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )

    response = client.post(
        new_page_url,
        data={
            "status": "REVIEW",
            "title": "Seite, die zur Freigabe vorgelegt wird",
            "slug": "seite-zur-freigabe",
            "content": "<p>Seite, die zur Freigabe vorgelegt wird</p>",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "left",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "organization": "",
        },
    )

    assert response.status_code == 302
    page_edit_url = response.headers.get("location")

    response = client.get(page_edit_url)

    assert response.status_code == 200
    assert (
        "Seite &quot;Seite, die zur Freigabe vorgelegt wird&quot; wurde erfolgreich erstellt und zur Freigabe vorgelegt"
        in response.content.decode("utf-8")
    )


@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.django_db
def test_no_changes_but_updated_message(
    login_role_user: tuple[Client, str],
):
    client, role = login_role_user

    # Url to create a new page
    new_page_url = reverse(
        "new_page",
        kwargs={
            "region_slug": "augsburg",
            "language_slug": "de",
        },
    )

    response = client.post(
        new_page_url,
        data={
            "status": "PUBLIC",
            "title": "Seite ohne Änderung",
            "slug": "seite-ohne-änderung",
            "content": "<p>Seite ohne Änderung</p>",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "right",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
        },
    )

    assert response.status_code == 302
    page_edit_url = response.headers.get("location")

    response = client.post(
        page_edit_url,
        data={
            "status": "PUBLIC",
            "title": "Seite ohne Änderung",
            "slug": "seite-ohne-änderung",
            "content": "<p>Seite ohne Änderung</p>",
            "icon": "",
            "_ref_node_id": 28,
            "_position": "right",
            "parent": "",
            "mirrored_page_region": "",
            "mirrored_page_first": True,
            "api_token": "",
            "authors": "",
            "editors": "",
            "organization": "",
            "minor_edit": False,
        },
    )

    assert response.status_code == 302
    assert response.headers.get("location") == page_edit_url

    response = client.get(page_edit_url)

    assert response.status_code == 200
    assert (
        "Keine Änderungen vorgenommen, aber Datum aktualisiert"
        in response.content.decode("utf-8")
    )
