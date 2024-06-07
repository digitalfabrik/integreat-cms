import json

import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import resolve, reverse

from integreat_cms.cms.models.poi_categories.poi_category import POICategory
from integreat_cms.cms.models.pois.poi import POI
from tests.conftest import ANONYMOUS, CMS_TEAM, ROOT, SERVICE_TEAM, STAFF_ROLES

DEFAULT_POST_DATA = {
    "icon": "daily_routine",
    "color": "#1DC6C6",
    "translations-0-language": "8",
    "translations-1-language": "3",
    "translations-2-language": "1",
    "translations-3-language": "6",
    "translations-4-language": "10",
    "translations-5-language": "2",
    "translations-6-language": "5",
    "translations-7-language": "4",
    "translations-8-language": "7",
    "translations-9-language": "9",
    "translations-TOTAL_FORMS": "10",
    "translations-INITIAL_FORMS": "0",
    "translations-MIN_NUM_FORMS": "10",
    "translations-MAX_NUM_FORMS": "10",
}


@pytest.mark.django_db
def test_permission_to_view_poi_categories_list(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    poicategories = reverse("poicategories")
    response = client.get(poicategories)

    if role in STAFF_ROLES:
        assert response.status_code == 200
        assert "Ortskategorien" in response.content.decode("utf-8")
    elif role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={poicategories}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.parametrize("login_role_user", STAFF_ROLES, indirect=True)
@pytest.mark.django_db
def test_poicategories_list_shows_all_items(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, _ = login_role_user
    poicategories = reverse("poicategories")
    response = client.get(poicategories)
    existing_poi_categories = POICategory.objects.all()
    for poi_category in existing_poi_categories:
        assert poi_category.name in response.content.decode("utf-8")


@pytest.mark.django_db
def test_correct_number_of_poicategories_in_database() -> None:
    expected_number_of_poicategories = 3
    actual_number_of_poicategories_in_database = POICategory.objects.count()
    assert (
        expected_number_of_poicategories == actual_number_of_poicategories_in_database
    )


@pytest.mark.django_db
def test_permission_to_create_new_poicategory(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user

    new_poicategory = reverse("new_poicategory")

    response = client.get(new_poicategory)
    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={new_poicategory}"
        )

    if role not in STAFF_ROLES and not ANONYMOUS:
        assert response.status_code == 403

    if role in STAFF_ROLES:
        assert response.status_code == 200
        assert "Neue Ortskategorie erstellen" in response.content.decode("utf-8")


@pytest.mark.parametrize(
    "login_role_user", [CMS_TEAM, ROOT, SERVICE_TEAM], indirect=True
)
@pytest.mark.django_db
def test_create_poi_category_with_missing_translation_was_not_successful(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user

    new_poicategory_url = reverse("new_poicategory")

    response = client.post(
        new_poicategory_url,
        data={
            "icon": "education",
            "color": "#1DC6C6",
        },
    )

    assert response.status_code == 200
    assert "Mindestens eine Übersetzung ist erforderlich." in response.content.decode(
        "utf-8"
    )


@pytest.mark.parametrize(
    "login_role_user", [CMS_TEAM, ROOT, SERVICE_TEAM], indirect=True
)
@pytest.mark.django_db
def test_create_poi_category_was_successful(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, _ = login_role_user

    new_poicategory_url = reverse("new_poicategory")

    response = client.post(
        new_poicategory_url,
        data=DEFAULT_POST_DATA | {"translations-2-name": "Neu erstellte Ortskategorie"},
    )

    edit_url = response.headers.get("location")
    assert response.status_code == 302

    id_of_poicategory = resolve(edit_url).kwargs["pk"]

    response = client.get(edit_url)
    assert response.status_code == 200
    assert (
        "Ortskategorie &quot;Neu erstellte Ortskategorie&quot; wurde erfolgreich erstellt"
        in response.content.decode("utf-8")
    )
    assert POICategory.objects.get(id=id_of_poicategory) is not None


@pytest.mark.parametrize(
    "login_role_user", [CMS_TEAM, ROOT, SERVICE_TEAM], indirect=True
)
@pytest.mark.django_db
def test_edit_poi_category_was_successful(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, _ = login_role_user

    new_poicategory_url = reverse("new_poicategory")

    response = client.post(
        new_poicategory_url,
        data=DEFAULT_POST_DATA | {"translations-2-name": "Neu erstellte Ortskategorie"},
    )

    edit_url = response.headers.get("location")
    assert response.status_code == 302

    id_of_poicategory = resolve(edit_url).kwargs["pk"]

    poicategory = POICategory.objects.get(id=id_of_poicategory)
    translation = poicategory.translations.get(language__slug="de")

    response = client.post(
        edit_url,
        data={
            "icon": "daily_routine",
            "color": "#1DC6C6",
            "translations-0-category": str(poicategory.id),
            "translations-0-language": "1",
            "translations-0-id": str(translation.id),
            "translations-0-name": "Umbenannte Ortskategorie",
            "translations-1-language": "8",
            "translations-2-language": "3",
            "translations-3-language": "6",
            "translations-4-language": "10",
            "translations-5-language": "2",
            "translations-6-language": "5",
            "translations-7-language": "4",
            "translations-8-language": "7",
            "translations-9-language": "9",
            "translations-TOTAL_FORMS": "10",
            "translations-INITIAL_FORMS": "1",
            "translations-MIN_NUM_FORMS": "10",
            "translations-MAX_NUM_FORMS": "10",
        },
    )

    assert response.status_code == 302
    response = client.get(edit_url)
    assert response.status_code == 200

    assert (
        "Ortskategorie &quot;Neu erstellte Ortskategorie&quot; wurde erfolgreich gespeichert"
        in response.content.decode("utf-8")
    )
    translation = poicategory.translations.get(language__slug="de")
    assert translation.name == "Umbenannte Ortskategorie"


@pytest.mark.parametrize(
    "login_role_user", [CMS_TEAM, ROOT, SERVICE_TEAM], indirect=True
)
@pytest.mark.django_db
def test_no_changes_were_made_message(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, _ = login_role_user

    new_poicategory_url = reverse("new_poicategory")

    response = client.post(
        new_poicategory_url,
        data=DEFAULT_POST_DATA
        | {"translations-2-name": "Nicht veränderte Ortskategorie"},
    )

    edit_url = response.headers.get("location")
    assert response.status_code == 302

    id_of_poicategory = resolve(edit_url).kwargs["pk"]

    poicategory = POICategory.objects.get(id=id_of_poicategory)
    translation = poicategory.translations.get(language__slug="de")

    response = client.post(
        edit_url,
        data={
            "icon": "daily_routine",
            "color": "#1DC6C6",
            "translations-0-category": str(poicategory.id),
            "translations-0-language": "1",
            "translations-0-id": str(translation.id),
            "translations-0-name": "Nicht veränderte Ortskategorie",
            "translations-1-language": "8",
            "translations-2-language": "3",
            "translations-3-language": "6",
            "translations-4-language": "10",
            "translations-5-language": "2",
            "translations-6-language": "5",
            "translations-7-language": "4",
            "translations-8-language": "7",
            "translations-9-language": "9",
            "translations-TOTAL_FORMS": "10",
            "translations-INITIAL_FORMS": "1",
            "translations-MIN_NUM_FORMS": "10",
            "translations-MAX_NUM_FORMS": "10",
        },
    )

    assert response.status_code == 302
    response = client.get(edit_url)
    assert response.status_code == 200

    assert "Keine Änderungen vorgenommen" in response.content.decode("utf-8")


@pytest.mark.parametrize(
    "login_role_user", [CMS_TEAM, ROOT, SERVICE_TEAM], indirect=True
)
@pytest.mark.django_db
def test_delete_unused_poi_category_was_successful(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    current_amount_of_poicategories = POICategory.objects.count()
    expected_amount_of_poicategories = current_amount_of_poicategories
    client, _ = login_role_user

    new_poicategory_url = reverse("new_poicategory")

    response = client.post(
        new_poicategory_url,
        data=DEFAULT_POST_DATA
        | {"translations-2-name": "Neu erstellte, zu löschende Ortskategorie"},
    )

    edit_url = response.headers.get("location")
    id_of_unused_poicategory = resolve(edit_url).kwargs["pk"]

    amount_of_poicategories = POICategory.objects.count()
    assert amount_of_poicategories == expected_amount_of_poicategories + 1

    delete_poicategory_url = reverse(
        "delete_poicategory", kwargs={"pk": id_of_unused_poicategory}
    )

    client.post(delete_poicategory_url, data={})
    amount_of_poicategories = POICategory.objects.count()
    assert amount_of_poicategories == expected_amount_of_poicategories


@pytest.mark.parametrize(
    "login_role_user", [CMS_TEAM, ROOT, SERVICE_TEAM], indirect=True
)
@pytest.mark.django_db
def test_delete_used_poi_category_was_not_successful(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    current_amount_of_poicategories = POICategory.objects.count()
    expected_amount_of_poicategories = current_amount_of_poicategories + 1
    client, _ = login_role_user

    new_poicategory_url = reverse("new_poicategory")
    response = client.post(
        new_poicategory_url,
        data=DEFAULT_POST_DATA
        | {"translations-2-name": "Neu erstellte, zu löschende Ortskategorie"},
    )

    amount_of_poicategories = POICategory.objects.count()
    assert amount_of_poicategories == expected_amount_of_poicategories

    edit_url = response.headers.get("location")
    id_of_unused_poicategory = resolve(edit_url).kwargs["pk"]

    new_poicategory = POICategory.objects.get(id=id_of_unused_poicategory)

    POI.objects.create(
        region_id=1,
        address="Wertachstraße 29",
        postcode="86150",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=new_poicategory,
    )

    delete_poicategory_url = reverse(
        "delete_poicategory", kwargs={"pk": id_of_unused_poicategory}
    )
    response = client.post(delete_poicategory_url, data={})
    redirect = response.headers.get("location")
    assert response.status_code == 302
    response = client.get(redirect)

    amount_of_poicategories = POICategory.objects.count()

    assert amount_of_poicategories == expected_amount_of_poicategories
    assert (
        "Diese Kategorie kann nicht gelöscht werden, da sie von mindestens einem Ort verwendet wird."
        in response.content.decode("utf-8")
    )
