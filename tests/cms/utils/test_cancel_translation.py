import pytest
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.constants import translation_status
from integreat_cms.cms.models.pages.page_translation import PageTranslation
from tests.conftest import EDITOR, MANAGEMENT, PRIV_STAFF_ROLES


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_role_user", PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR], indirect=True  # Rollen
)
@pytest.mark.parametrize("page_ids", [[30, 31]])
def test_page_bulk_actions(
    load_test_data: None,
    page_ids: list[int],
    login_role_user: tuple[Client, str],
) -> None:

    client, _ = login_role_user

    kwargs = {"region_slug": "augsburg", "language_slug": "de"}
    cancel_translation_process = reverse("cancel_translation_process", kwargs=kwargs)
    response = client.post(
        cancel_translation_process, data={"selected_ids[]": page_ids}
    )
    assert response.status_code == 302

    for page_id in page_ids:
        translation = PageTranslation.objects.get(page__id=page_id)
        assert translation.translation_state != translation_status.IN_TRANSLATION
