from __future__ import annotations

from datetime import datetime

import pytest
from dateutil.relativedelta import relativedelta
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import (
    Language,
    PushNotification,
    PushNotificationTranslation,
    Region,
)

REGION_SLUG = "artland"


def create_a_pushnotification(region_slug: str) -> tuple[int, int]:
    """
    A function to create a new push notification and a translation in the default language of the region.
    """
    region = Region.objects.get(slug=region_slug)
    default_language = Language.objects.get(slug=region.default_language.slug)
    pushnotification = PushNotification.objects.create(
        channel="news",
        sent_date=datetime.now() - relativedelta(days=1),
        created_date=datetime.now() - relativedelta(days=1),
        scheduled_send_date=None,
    )
    pushnotification.regions.add(region)
    pushnotification.save()
    pushnotification_translation = PushNotificationTranslation.objects.create(
        title="German Traslation",
        text="Hello World",
        language=default_language,
        push_notification=pushnotification,
        last_updated=datetime.now() - relativedelta(days=1),
    )
    pushnotification_translation.save()

    return pushnotification.id, pushnotification_translation.id


@pytest.mark.django_db
def test_no_archived_pushnotification(load_test_data: None) -> None:
    """
    Check that archived push notifications are excluded from the API result

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """

    client = Client()

    kwargs = {"region_slug": REGION_SLUG, "language_slug": "de"}
    api = reverse("api:sent_push_notifications", kwargs=kwargs)
    start_response = client.get(api)
    start_result = start_response.content.decode("utf-8")

    pushnotification_id, pushnotification_translation_id = create_a_pushnotification(
        REGION_SLUG
    )

    response_after_new_pn = client.get(api)
    result_after_new_pn = response_after_new_pn.content.decode("utf-8")
    assert (
        f'"id": {pushnotification_translation_id}, "title": "German Traslation", "message": "Hello World"'
        in result_after_new_pn
    )

    pushnotification = PushNotification.objects.get(id=pushnotification_id)
    pushnotification.archived = True
    pushnotification.save()

    response_after_archiving = client.get(api)
    result_after_archiving = response_after_archiving.content.decode("utf-8")
    assert result_after_archiving == start_result
