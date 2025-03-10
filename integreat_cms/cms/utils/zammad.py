"""
Zammad API helper functions
"""

from abc import abstractmethod
from typing import TYPE_CHECKING

import requests
from django.conf import settings
from django.utils.functional import cached_property

if TYPE_CHECKING:
    from ..models import Region


class ZammadAPI:
    """
    Zammad API Wrapper. This is intended to be used as a UserChat parent class.
    """

    @property
    @abstractmethod
    def zammad_id(self) -> int:
        """
        Property that has to be defined in child classes
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def region(self) -> "Region":
        """
        Property that has to be defined in child classes
        """
        raise NotImplementedError

    def zammad_request(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
    ) -> requests.Response:
        """
        Wrapper for calling the Zammad API. Mostly takes care of auth and timeout.

        :param method: HTTP Method
        :param path: API path that will be called
        :param payload: JSON payload as dict
        :return: Response from Zammad API
        """
        return requests.request(
            method=method,
            url=f"{self.region.zammad_url}{path}",
            timeout=5,
            headers={"Authorization": self.region.zammad_access_token},
            json=payload,
        )

    def get_zammad_user_mail(self) -> str:
        """
        Get Zammad user e-mail

        :param region: region that is connected to the Zammad server
        :return: User e-mail address
        """
        return self.zammad_request("GET", "/api/v1/users/me").json()["login"]

    def get_zammad_ticket_messages(self) -> list[dict]:
        """
        Get Zammad ticket articles

        :return: list of Zammad articles (chat messages)
        """
        return self.zammad_request(
            "GET",
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
        formatted_messages = []
        for message in response:
            formatted_message = {
                key: message[key] for key in keys_to_keep if key in message
            }
            if message["user_is_author"]:
                formatted_message["role"] = "user"
            else:
                formatted_message["role"] = "agent"
            formatted_message["content"] = message["body"]
            formatted_messages.append(message)
        return formatted_messages

    def save_message(
        self, message: str, internal: bool, automatic_message: bool
    ) -> bool:
        """
        Add a new message

        :param message: message text to be saved
        :param internal: true if message shoud not be visible to app user
        :param automatic_message: true if message does not originate from a human
        :return: success
        """
        del self.messages
        return (
            self.zammad_request(
                "POST",
                "/api/v1/ticket_articles",
                {
                    "ticket_id": self.zammad_id,
                    "body": message,
                    "internal": internal,
                    "automatic_message": automatic_message,
                    "content_type": "text/html",
                    "type": "web",
                    "sender": "Customer" if not automatic_message else "Agent",
                },
            ).status_code
            == 200
        )

    @cached_property
    def evaluation_consent(self) -> bool:
        """
        Get user evaluation consent

        :return: user evaluation consent
        """
        return self.zammad_request(
            "GET",
            f"/api/v1/tickets/{self.zammad_id}",
        ).json()["evaluation_consent"]

    def save_evaluation_consent(self, value: bool) -> bool:
        """
        Set user evaluation consent

        :param value: True if user agrees, false if not
        :return: success
        """
        del self.evaluation_consent
        return (
            self.zammad_request(
                "POST",
                f"/api/v1/tickets/{self.zammad_id}",
                {"evaluation_consent": value},
            ).status_code
            == 200
        )

    @cached_property
    def automatic_answers(self) -> bool:
        """
        Check if automatic answers are turned on/off

        :return: generate automatic answers or not
        """
        return self.zammad_request(
            "GET",
            f"/api/v1/tickets/{self.zammad_id}",
        ).json()["automatic_answers"]

    def save_automatic_answers(self, value: bool) -> bool:
        """
        Turn automatic answers on/off

        :param value: True if user agrees, false if not
        :return: success
        """
        del self.automatic_answers
        return (
            self.zammad_request(
                "POST",
                f"/api/v1/tickets/{self.zammad_id}",
                {"automatic_answers": value},
            ).status_code
            == 200
        )

    def create_ticket(self, title: str) -> int:
        """
        Create Zammad ticket and return ticket ID

        :param title: Ticket title
        :return: Zammad ticket ID
        """
        return self.zammad_request(
            "POST",
            "/api/v1/",
            {
                "title": title,
                "group": settings.USER_CHAT_TICKET_GROUP,
                "customer": self.get_zammad_user_mail(),
            },
        ).json()["ticket_id"]
