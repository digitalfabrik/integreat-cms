from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import patch

import requests

if TYPE_CHECKING:
    from typing import Any

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from pytest_django.fixtures import SettingsWrapper
from requests_mock.mocker import Mocker

from integreat_cms.cms.models import (
    Language,
    LanguageTreeNode,
    PushNotification,
    PushNotificationTranslation,
    Region,
)
from integreat_cms.firebase_api.firebase_api_client import FirebaseApiClient

from ..utils import get_command_output


class TestSendPushNotification:
    """
    Test that cover the send_push_notification management command and its filter mechanisms
    """

    @pytest.mark.django_db
    def test_push_notifications_disabled(self, settings: SettingsWrapper) -> None:
        """
        Ensure that disabled push notifications cause an error
        """
        settings.FCM_ENABLED = False
        with pytest.raises(CommandError) as exc_info:
            assert not any(get_command_output("send_push_notifications"))
        assert str(exc_info.value) == "Push notifications are disabled"

    @pytest.mark.django_db
    def test_push_notifications_nonexisting_testregion(
        self,
        settings: SettingsWrapper,
    ) -> None:
        """
        Ensure that an error is caused when the system runs in debug mode but the test region does not exist
        """
        settings.TEST_REGION_SLUG = "non-existing"
        settings.DEBUG = True
        with pytest.raises(CommandError) as exc_info:
            assert not any(get_command_output("send_push_notifications"))
        assert (
            str(exc_info.value)
            == f"The system runs with DEBUG=True but the region with TEST_REGION_SLUG={settings.TEST_REGION_SLUG} does not exist."
        )

    patch: Any = None

    def setup_method(self) -> None:
        self.patch = patch.object(
            FirebaseApiClient, "_get_access_token", return_value="secret access token"
        )
        self.patch.start()

    def teardown_method(self) -> None:
        self.patch.stop()
        self.patch = None

    @pytest.mark.django_db
    def test_ignore_overdue_notification(
        self, settings: SettingsWrapper, requests_mock: Mocker
    ) -> None:
        called = 0

        def json_func(
            _request: requests.PreparedRequest, _context: Any
        ) -> dict[str, str | int]:
            nonlocal called
            called += 1

            return {
                "name": "projects/integreat-2020/messages/1",
                "status_code": 200,
            }

        requests_mock.post(
            "https://fcm.googleapis.com/v1/projects/integreat-2020/messages:send",
            json=json_func,
            status_code=200,
        )

        german_language = Language.objects.create(
            slug="de-test",
            bcp47_tag="de",
            native_name="Deutsch",
            english_name="German",
            text_direction="ltr",
            primary_country_code="DE",
            table_of_contents="Inhaltsverzeichnis",
        )

        region = Region.objects.create(name="unit-test-region")

        LanguageTreeNode.objects.create(
            language=german_language, lft=1, rgt=2, tree_id=1, depth=1, region=region
        )

        push_notification = PushNotification.objects.create(
            channel="default",
            draft=False,
            sent_date=None,
            scheduled_send_date=datetime.now(),
            mode="ONLY_AVAILABLE",
            is_template=False,
            template_name=None,
        )

        overdue_push_notification = PushNotification.objects.create(
            channel="default",
            draft=False,
            sent_date=None,
            scheduled_send_date=datetime.now() - timedelta(days=2),
            mode="ONLY_AVAILABLE",
            is_template=False,
            template_name=None,
        )

        PushNotificationTranslation.objects.create(
            title="Test Push Notification",
            text="Test Push Notification",
            push_notification=push_notification,
            language=german_language,
        )

        PushNotificationTranslation.objects.create(
            title="Test (Overdue) Push Notification",
            text="Test Push Notification",
            push_notification=overdue_push_notification,
            language=german_language,
        )

        push_notification.regions.add(region)
        push_notification.save()

        overdue_push_notification.regions.add(region)
        overdue_push_notification.save()

        call_command("send_push_notifications")

        assert called == 1
