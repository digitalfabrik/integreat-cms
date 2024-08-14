import logging
from collections import defaultdict
from typing import Dict, Union

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from integreat_cms.firebase_api.firebase_security_service import FirebaseSecurityService

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
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
                "Push notifications are disabled, so are the analytics"
            )

        self.endpoint_url = settings.FCM_DATA_URL

    def fetch_notification_statistics(
        self,
    ) -> Dict[str, Dict[str, Union[int, Dict[str, int]]]]:
        """
        Fetches messaging statistics from the Firebase API and calculates the total counts of notifications sent per region
        and per language within the returned timespan.

        Returns:
            Dict[str, Dict[str, Union[int, Dict[str, int]]]]:
                A dictionary where each key is a region and each value is another dictionary with:
                - "total": The total number of notifications accepted in the region.
                - "languages": A dictionary of languages within the region, with each language's total number of notifications.
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
            return {}

        response_data = response.json().get("androidDeliveryData", [])

        region_data: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for item in response_data:
            if "countNotificationsAccepted" in item["data"]:
                analytics_label = item.get("analyticsLabel")
                count_accepted = int(item["data"]["countNotificationsAccepted"])
                if analytics_label:
                    region, language = analytics_label.split("-")
                    region_data[region][language] += count_accepted

        output: Dict[str, Dict[str, Union[int, Dict[str, int]]]] = {
            region: {"total": sum(languages.values()), "languages": languages}
            for region, languages in region_data.items()
        }

        return output
