import google.auth
from django.conf import settings
from google.oauth2 import service_account


class FirebaseSecurityService:
    """
    Service to generate access tokens that can be used for different firebase endpoints like messaging or data.
    """

    @staticmethod
    def get_messaging_access_token() -> str:
        """
        Retrieve a valid access token that can be used to authorize requests against the messaging api.

        :return: Fresh Access token
        """

        return FirebaseSecurityService._get_access_token(
            "https://www.googleapis.com/auth/firebase.messaging",
        )

    @staticmethod
    def get_data_access_token() -> str:
        """
        Retrieve a valid access token that can be used to authorize requests against the messaging data api.

        :return: Fresh Access token
        """

        return FirebaseSecurityService._get_access_token(
            "https://www.googleapis.com/auth/cloud-platform",
        )

    @staticmethod
    def _get_access_token(scope: str) -> str:
        """
        Retrieve a valid access token that can be used to authorize requests.
        This function is taken from https://github.com/firebase/quickstart-python/blob/2c68e7c5020f4dbb072cca4da03dba389fbbe4ec/messaging/messaging.py#L26-L35

        :return: Access token
        """
        credentials = service_account.Credentials.from_service_account_file(
            settings.FCM_CREDENTIALS,
            scopes=[scope],
        )
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        return credentials.token
