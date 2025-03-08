"""
Zammad API helper functions
"""

import requests

from django.conf import settings
from django.utils.functional import cached_property

from ..models import Region

def zammad_request(
        method: str, region: Region, path: str, payload: dict = None
    ) -> requests.Response:
    """
    Wrapper for calling the Zammad API. Mostly takes care of auth and timeout.
    
    :param method: HTTP Method
    :param region: Region to which the chat/Zammad belongs
    :param path: API path that will be called
    :param payload: JSON payload as dict
    :return: Response from Zammad API
    """
    return requests.request(
            method=method,
            url=f"{region.zammad_url}{path}",
            timeout=5,
            headers={'Authorization': region.zammad_access_token},
            json=payload
        )

def get_zammad_user_mail(region: Region) -> str:
    """
    Get Zammad user e-mail

    :param region: region that is connected to the Zammad server
    :return: User e-mail address
    """
    return zammad_request("GET", region, "/api/v1/users/me").json()["login"]


class ZammadAPI:
    """
    Zammad API Wrapper. This is intended to be used as a UserChat parent class.
    """

    zammad_id = None
    region = None

    def get_zammad_ticket_messages(self) -> list[dict]:
        """
        Get Zammad ticket articles

        :return: list of Zammad articles (chat messages)
        """
        return zammad_request(
            "GET",
            self.region,
            f"/api/v1/ticket_articles/by_ticket/{self.zammad_id}",
        ).json()

    @cached_property
    def messages(self) -> list[dict]:
        """
        Return all messages stored in Zammad for this ticket

        :return: formatted chat messages
        """
        response = self.get_zammad_ticket_messages()
        keys_to_keep = [
            "status",
            "error",
            "id",
            "body",
            "user_is_author",
            "automatic_answer",
            "evaluation_consent",
        ]
        response = {key: response[key] for key in keys_to_keep if key in response}
        response["content"] = response["body"]
        formatted_messages = []
        for message in response:
            if message["user_is_author"]:
                message["role"] = "user"
            else:
                message["role"] = "agent"
            message["content"] = message["body"]
            formatted_messages.append(message)
        return formatted_messages

    def save_message(self, message: str, internal: bool, automatic_message: bool):
        """
        Add a new message
        """
        del self.messages
        return zammad_request(
            "POST",
            self.region,
            "/api/v1/ticket_articles",
            {
                "ticket_id": self.zammad_id,
                "body": message,
                "internal": internal,
                "automatic_message": automatic_message,
                "content_type": "text/html",
                "type": "web",
                "sender": "Customer" if not automatic_message else "Agent",
            }
        ).status_code == 200

    @cached_property
    def evaluation_consent(self) -> bool:
        """
        Get user evaluation consent
        """
        return zammad_request(
            "GET", self.region, f"/api/v1/tickets/{self.zammad_id}"
        ).json()["evaluation_consent"]

    @evaluation_consent.setter
    def evaluation_consent(self, value: bool) -> None:
        """
        Set user evaluation consent

        :param value: True if user agrees, false if not
        :return
        """
        del self.evaluation_consent
        return zammad_request(
            "POST", self.region, f"/api/v1/tickets/{self.zammad_id}", {"evaluation_consent": value}
        ).status_code == 200

    @cached_property
    def automatic_answers(self) -> bool:
        """
        Check if automatic answers are turned on/off
        """
        return zammad_request(
            "GET", self.region, f"/api/v1/tickets/{self.zammad_id}"
        ).json()["automatic_answers"]

    @automatic_answers.setter
    def automatic_answers(self, value: bool) -> None:
        """
        Turn automatic answers on/off

        :param value: True if user agrees, false if not
        :return
        """
        del self.automatic_answers
        return zammad_request(
            "POST", self.region, f"/api/v1/tickets/{self.zammad_id}", {"automatic_answers": value}
        ).status_code == 200

    def create_ticket(self, region: Region, title: str) -> int:
        """
        Create Zammad ticket and return ticket ID

        :param region: Region to which the Zammad belongs
        :param title: Ticket title
        :return: Zammad ticket ID
        """
        return zammad_request(
            "POST",
            region,
            "/api/v1/",
            {
                "title": title,
                "group": settings.USER_CHAT_TICKET_GROUP,
                "customer": get_zammad_user_mail(region)
            }
        ).json()["ticket_id"]
