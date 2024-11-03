import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models.pages.page import Page
from integreat_cms.cms.models.regions.region import Region
from tests.conftest import ANONYMOUS, CMS_TEAM, ROOT, SERVICE_TEAM


@pytest.mark.django_db
def test_delete_all_regions_is_successful(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    current_number_of_regions = Region.objects.count()
    client, role = login_role_user

    # Deletion of Augsburg will not be possible due to a cloned page in Nurnberg.
    # We want to test this is in the test below. In this test we want to make sure this is the only reason why deleting is not possible.
    cloned_page = Page.objects.filter(id=30)
    cloned_page.delete()

    assert current_number_of_regions > 0

    # We want to test with existing data, as we want to make sure as many dependencies as possible are covered
    for region in Region.objects.all():
        delete_region = reverse("delete_region", kwargs={"slug": region.slug})
        response = client.post(delete_region, data={})

        if role == ANONYMOUS:
            assert response.status_code == 302
            assert (
                response.headers.get("location")
                == f"{settings.LOGIN_URL}?next={delete_region}"
            )
            return

        if role not in [CMS_TEAM, SERVICE_TEAM, ROOT] and not ANONYMOUS:
            assert response.status_code == 403
            continue

        if role in [CMS_TEAM, SERVICE_TEAM, ROOT]:
            assert response.status_code == 302
            redirect = response.headers.get("location")
            response = client.get(redirect)

    if role in [CMS_TEAM, SERVICE_TEAM, ROOT]:
        assert Region.objects.count() == 0


@pytest.mark.django_db
def test_deleting_mirrored_region_is_unsucessful(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user

    augsburg = Region.objects.get(slug="augsburg")
    cloned_page = Page.objects.filter(id=30)
    assert cloned_page.exists()

    delete_region = reverse("delete_region", kwargs={"slug": augsburg.slug})
    response = client.post(delete_region, data={})

    if role == ANONYMOUS:
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={delete_region}"
        )

    if role not in [CMS_TEAM, SERVICE_TEAM, ROOT] and not ANONYMOUS:
        assert response.status_code == 403

    if role in [CMS_TEAM, SERVICE_TEAM, ROOT]:
        assert response.status_code == 302
        redirect = response.headers.get("location")
        response = client.get(redirect)
        assert (
            "Die Region konnte nicht gelöscht werden, weil die folgenden Seiten in anderen Region gespiegelt werden:"
            in response.content.decode("utf-8")
        )
        assert Region.objects.filter(slug="augsburg").exists()
