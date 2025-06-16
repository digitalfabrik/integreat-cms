from datetime import timedelta

import pytest
from django.test.client import Client
from django.utils import timezone

from integreat_cms.cms.models import Event, ExternalCalendar, Region
from integreat_cms.cms.models.events.event import CouldNotBeCopied


@pytest.mark.django_db
def test_copying_imported_event_is_unsucessful(
    test_data_db_snapshot: None,
    db_snapshot: None,
    login_role_user: tuple[Client, str],
) -> None:
    _, role = login_role_user
    region = Region.objects.create(name="Testregion")

    external_calendar = ExternalCalendar.objects.create(
        name="Test external calendar",
        region=region,
    )

    new_event = Event.objects.create(
        start=timezone.now(),
        end=timezone.now() + timedelta(days=1),
        region=region,
        external_calendar=external_calendar,
    )

    with pytest.raises(CouldNotBeCopied) as e:
        new_event.copy(role)
        assert (
            str(e.value)
            == "Event couldn't be copied because it's from a external calendar"
        )
