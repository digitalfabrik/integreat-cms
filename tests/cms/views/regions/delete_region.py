import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models.feedback.page_feedback import PageFeedback
from integreat_cms.cms.models.feedback.poi_feedback import POIFeedback
from integreat_cms.cms.models.media.media_file import MediaFile
from integreat_cms.cms.models.pages.page import Page
from integreat_cms.cms.models.push_notifications.push_notification import (
    PushNotification,
)
from integreat_cms.cms.models.regions.region import Region
from tests.conftest import ANONYMOUS, CMS_TEAM, ROOT, SERVICE_TEAM

CLONED_PAGE = 30
NESTED_MEDIA_OBJECT_ID = 1
POI_FEEDBACK_AUGSBURG_ID = 6
PAGE_FEEDBACK_AUGSBURG_ID = 2


@pytest.mark.django_db
def test_delete_all_regions_is_successful(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    current_number_of_regions = Region.objects.count()
    assert current_number_of_regions > 0

    client, role = login_role_user

    # We want to test regions can be deleted even if they have feedback and/or nested media object
    # See #2462 for details: IntegrityError when there are 2 feedback with different endpoint
    assert POIFeedback.objects.filter(id=POI_FEEDBACK_AUGSBURG_ID).first()
    assert PageFeedback.objects.filter(id=PAGE_FEEDBACK_AUGSBURG_ID).first()
    # See 1749 for details: ProtectedError when a subfolder in a media library has contents
    nested_media_object = MediaFile.objects.filter(id=NESTED_MEDIA_OBJECT_ID).first()
    assert nested_media_object
    assert nested_media_object.parent_directory.id

    # Users that will be deleted after all the regions are deleted
    assert (
        get_user_model().objects.filter(is_superuser=False, is_staff=False).count() > 0
    )

    # Deletion of Augsburg will not be possible due to a cloned page in Nurnberg.
    # We want to test this is in the test below. In this test we want to make sure this is the only reason why deleting is not possible.
    cloned_page = Page.objects.filter(id=CLONED_PAGE)
    cloned_page.delete()

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
            assert "Region wurde erfolgreich gelöscht" in response.content.decode(
                "utf-8"
            )

    if role in [CMS_TEAM, SERVICE_TEAM, ROOT]:
        assert Region.objects.count() == 0
        # No users without region
        assert (
            get_user_model()
            .objects.filter(is_superuser=False, is_staff=False, regions=None)
            .count()
            == 0
        )
        # No push notification without region
        assert PushNotification.objects.filter(regions=None).count() == 0


@pytest.mark.django_db
def test_deleting_mirrored_region_is_unsucessful(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user

    augsburg = Region.objects.get(slug="augsburg")
    cloned_page = Page.objects.filter(id=CLONED_PAGE)
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
            "Die Region konnte nicht gelöscht werden, weil die folgenden Seiten in anderen Regionen gespiegelt werden:"
            in response.content.decode("utf-8")
        )
        assert Region.objects.filter(slug="augsburg").exists()
