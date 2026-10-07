from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from integreat_cms.cms.models import PushNotification
from tests.constants import ANONYMOUS

if TYPE_CHECKING:
    from django.test.client import Client

PUSH_NOTIFICATION_ID = 2
URL_KWARGS = {"region_slug": "augsburg", "language_slug": "de"}
COPY_URL = reverse(
    "copy_push_notification",
    kwargs={"push_notification_id": PUSH_NOTIFICATION_ID, **URL_KWARGS},
)


@pytest.mark.django_db
@pytest.mark.parametrize("archived", [True, False])
def test_copy_push_notification(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    archived: bool,
) -> None:
    """
    Archived news must neither show a copy button nor be copyable,
    while other news can still be copied (see #4234).
    """
    client, role = login_role_user
    if role == ANONYMOUS:
        pytest.skip("Anonymous users are redirected to the login")

    PushNotification.objects.filter(id=PUSH_NOTIFICATION_ID).update(archived=archived)
    list_url = reverse(
        "archived_push_notifications" if archived else "push_notifications",
        kwargs=URL_KWARGS,
    )
    count = PushNotification.objects.count()

    list_response = client.get(list_url)
    copy_response = client.get(COPY_URL)

    if not list_response.wsgi_request.user.has_perm("cms.change_pushnotification"):
        assert copy_response.status_code == 403
        assert PushNotification.objects.count() == count
        return

    assert list_response.status_code == 200
    if archived:
        assert COPY_URL not in list_response.content.decode("utf-8")
        assert copy_response.status_code == 404
        assert PushNotification.objects.count() == count
    else:
        assert COPY_URL in list_response.content.decode("utf-8")
        assert copy_response.status_code == 302
        assert PushNotification.objects.count() == count + 1
