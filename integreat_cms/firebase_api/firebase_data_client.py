import logging
from collections import defaultdict
from typing import Dict, Union

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

from integreat_cms.firebase_api.firebase_security_service import FirebaseSecurityService

logger = logging.getLogger(__name__)


class LanguageData:
    """
    Represents data related to a specific language, including the total count of accepted notifications
    and the number of days for which data is collected.

    Attributes:
        total (int): The total count of accepted notifications.
        days (int): The number of days for which data has been collected.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance of LanguageData with zero total notifications and days.
        """
        self.total = 0
        self.days = 0  # Keep track of the number of days

    def add(self, count_accepted: int) -> None:
        """
        Adds the count of accepted notifications for a day.

        Args:
            count_accepted (int): The number of notifications accepted on a particular day.
        """
        self.total += count_accepted
        self.days += 1  # Increment the day count

    def average(self) -> float:
        """
        Calculates the average number of notifications accepted per day.

        Returns:
            float: The average number of notifications accepted per day. Returns 0 if no days are recorded.
        """
        return self.total / self.days if self.days > 0 else 0


class RegionData:
    """
    Represents data related to a specific region, including the total count of accepted notifications
    and the number of days for which data is collected. It also tracks data for different languages within the region.

    Attributes:
        languages (Dict[str, LanguageData]): A dictionary mapping language codes to their respective LanguageData.
        total (int): The total count of accepted notifications in the region.
        total_days (int): The number of days for which data has been collected in the region.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance of RegionData with zero total notifications and days.
        """
        self.languages: Dict[str, LanguageData] = defaultdict(LanguageData)
        self.total = 0
        self.total_days = 0

    def add(self, language: str, count_accepted: int) -> None:
        """
        Adds the count of accepted notifications for a specific language.

        Args:
            language (str): The language code for which the notifications are accepted.
            count_accepted (int): The number of notifications accepted for the given language.
        """
        self.languages[language].add(count_accepted)
        self.total += count_accepted
        self.total_days += 1

    def get_averages(self) -> Dict[str, float]:
        """
        Gets the average number of notifications accepted per day for each language in the region.

        Returns:
            Dict[str, float]: A dictionary where the key is the language code and the value is the average number of notifications.
        """
        return {language: data.average() for language, data in self.languages.items()}

    def average(self) -> float:
        """
        Calculates the average number of notifications accepted per day in the region.

        Returns:
            float: The average number of notifications accepted per day in the region. Returns 0 if no days are recorded.
        """
        return self.total / self.total_days if self.total_days > 0 else 0


# pylint: disable=too-few-public-methods
class FirebaseDataClient:
    """
    A client for interacting with Firebase Cloud Messaging Data API.

    This class fetches messaging statistics and calculates averages for notifications sent per region and language.

    Documentation: https://firebase.google.com/docs/reference/fcmdata/rest
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

    def get_notification_statistics_per_region_and_language(
        self,
    ) -> Dict[str, Dict[str, Union[float, Dict[str, float]]]]:
        """
        Fetches messaging statistics from the Firebase API and calculates the average number of notifications sent per region
        and per language within the returned timespan.

        The data is cached to improve performance on subsequent requests.

        Returns:
            Dict[str, Dict[str, Union[float, Dict[str, float]]]]:
                A dictionary where each key is a region and each value is another dictionary with:
                - "average": The average number of notifications accepted per day in the region.
                - "languages": A dictionary of languages within the region, with each language's average number of notifications.
        """
        if (cached_data := cache.get("firebase_data")) is not None:
            return cached_data

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

        regions: Dict[str, RegionData] = defaultdict(RegionData)

        for item in response_data:
            if "countNotificationsAccepted" in item["data"]:
                analytics_label = item.get("analyticsLabel")
                count_accepted = int(item["data"]["countNotificationsAccepted"])
                if analytics_label:
                    region, language = analytics_label.split("-")
                    regions[region].add(language, count_accepted)

        output: Dict[str, Dict[str, Union[float, Dict[str, float]]]] = {
            region: {
                "average": region_data.average(),
                "languages": region_data.get_averages(),
            }
            for region, region_data in regions.items()
        }

        cache.set(
            "firebase_data",
            output,
            60 * 60 * 24 * 7,
        )

        return output
