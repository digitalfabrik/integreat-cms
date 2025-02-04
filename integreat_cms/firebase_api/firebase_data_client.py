import logging
from datetime import date

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from integreat_cms.firebase_api.firebase_security_service import FirebaseSecurityService

logger = logging.getLogger(__name__)


class FirebaseDataClient:
    """
    A client for interacting with Firebase Cloud Messaging Data API.

    This class ensures that Firebase access is enabled and provides methods to fetch and process notification statistics.
    """

    def __init__(self) -> None:
        """
        Initializes the FirebaseDataClient and checks if Firebase access is enabled.

        Raises:
            ImproperlyConfigured: If Firebase access is not enabled.
        """
        if not settings.FCM_ENABLED:
            raise ImproperlyConfigured(
                "Push notifications are disabled, so are the analytics",
            )

        self.endpoint_url = settings.FCM_DATA_URL

    def fetch_notification_statistics(
        self,
    ) -> list[dict[str, str | int]]:
        """
        Fetches messaging statistics from the Firebase API and calculates the counts of notifications sent per date,
        per region, and per language within the returned timespan.

        Returns:
            List[Dict[str, Union[str, int]]]:
                A list of dictionaries where each dictionary represents a FirebaseStatistic instance with keys:
                - "date": The date of the notifications.
                - "region": The region where notifications were sent.
                - "language_slug": The language slug for the notifications.
                - "count": The total number of notifications.
        """
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
            return []

        response_data = response.json().get("androidDeliveryData", [])

        statistics_list = []

        for item in response_data:
            if "countNotificationsAccepted" in item["data"]:
                analytics_label = item.get("analyticsLabel")
                date_info = item.get("date")

                date_obj = date(
                    date_info.get("year"),
                    date_info.get("month"),
                    date_info.get("day"),
                )

                count_accepted = int(item["data"]["countNotificationsAccepted"])
                if analytics_label:
                    region, language = analytics_label.split("-")
                    statistics_list.append(
                        {
                            "date": date_obj,
                            "region": region,
                            "language_slug": language,
                            "count": count_accepted,
                        },
                    )

        return statistics_list
