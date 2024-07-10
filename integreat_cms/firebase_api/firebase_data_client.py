import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from integreat_cms.firebase_api.firebase_security_service import FirebaseSecurityService

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class FirebaseDataCache:
    """
    Cache for the Firebase Cloud Messaging Data API Client
    """

    def __init__(self) -> None:
        """
        Initialize empty cache
        """
        self.data: Dict[Any, float | int] | None = None
        self.timestamp: datetime | None = None

    def is_valid(self) -> bool:
        """
        :return: Whether the cache contains a valid entry from today
        """
        if self.timestamp is None:
            return False

        return datetime.now().date() == self.timestamp.date()


# pylint: disable=too-few-public-methods
class FirebaseDataClient:
    """
    Firebase Cloud Messaging Data API Client

    Documentation: https://firebase.google.com/docs/reference/fcmdata/rest
    """

    def __init__(self) -> None:
        """
        Check if firebase access is enabled and initialize data

        :raises ~django.core.exceptions.ImproperlyConfigured: If firebase is disabled
        """

        if not settings.FCM_ENABLED:
            raise ImproperlyConfigured(
                "Push notifications are disabled, so are the analytics"
            )

        self.endpoint_url = settings.FCM_DATA_URL

        self.cache = FirebaseDataCache()

    def get_notification_statistics_per_region(self) -> dict[Any, float | int]:
        """
        Load messaging statistics and calculate the average sent messages per region within the returned timespan
        """

        # Check if cached data is valid for today
        if self.cache.data is not None and self.cache.is_valid():
            return self.cache.data

        headers = {
            "Authorization": f"Bearer {FirebaseSecurityService.get_data_access_token()}",
            "Content-Type": "application/json; UTF-8",
        }

        response = requests.get(
            self.endpoint_url,
            headers=headers,
            timeout=settings.DEFAULT_REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            return {}

        response_data = response.json().get("androidDeliveryData", [])

        label_totals: dict[str, dict[str, int]] = defaultdict(
            lambda: {"total": 0, "count": 0}
        )

        for item in response_data:
            if "countNotificationsAccepted" in item["data"]:
                analytics_label = item.get("analyticsLabel")
                count_accepted = int(item["data"]["countNotificationsAccepted"])
                if analytics_label:
                    label_totals[analytics_label]["total"] += count_accepted
                    label_totals[analytics_label]["count"] += 1

        averages = {
            label: data["total"] / data["count"] if data["count"] > 0 else 0
            for label, data in label_totals.items()
        }

        # Update cache
        self.cache.data = averages
        self.cache.timestamp = datetime.now()

        return averages
