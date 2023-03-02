import pytest
from django.test.client import Client
from django.urls import resolve, reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.models.pages.page_translation import PageTranslation
from tests.conftest import EDITOR, MANAGEMENT, PRIV_STAFF_ROLES


@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True
)
@pytest.mark.django_db
def test_cleanup_autosaves(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
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
            "status": "PUBLIC",
            "content": "",
            "title": "Autosave Page",
            "slug": "autosave-page",
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
    edit_page_url = response.headers.get("location")
    id_of_page = resolve(edit_page_url).kwargs["page_id"]

    translation = PageTranslation.objects.get(page__id=id_of_page)

    # autosaves which will later not exist anymore
    translation.pk = None
    translation.status = status.AUTO_SAVE
    translation.version = 2
    translation.save()

    translation.pk = None
    translation.status = status.AUTO_SAVE
    translation.version = 3
    translation.save()

    # first manual save
    translation.pk = None
    translation.status = status.PUBLIC
    translation.version = 4
    translation.save()

    # second autosave that should still be existing
    translation.pk = None
    translation.status = status.AUTO_SAVE
    translation.version = 5
    translation.save()

    # second manual save that should overwrite the first group of autosaves
    translation.pk = None
    translation.status = status.PUBLIC
    translation.version = 6
    translation.save()

    translation.cleanup_autosaves()

    # reload objects from database
    versions = translation.page.translations.all()
    assert len(versions) == 4

    # iterate through the versions and check if the correct versions are deleted/still there
    versions = list(reversed(versions))
    assert versions[0].status == status.PUBLIC
    assert versions[0].version == 1

    assert versions[1].status == status.PUBLIC
    assert versions[1].version == 2

    assert versions[2].status == status.AUTO_SAVE
    assert versions[2].version == 3

    # manual saves that should overwrite the one remaining autosave
    translation.pk = None
    translation.status = status.PUBLIC
    translation.version = 7
    translation.save()

    translation.pk = None
    translation.status = status.PUBLIC
    translation.version = 8
    translation.save()

    translation.cleanup_autosaves()
    versions = translation.page.translations.all()
    assert len(versions) == 5
