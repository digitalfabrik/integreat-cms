from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from django.http import HttpResponse

from django.conf import settings
from requests.exceptions import HTTPError
from zammad_py import ZammadAPI

from ....cms.models import AttachmentMap, Region, UserChat

logger = logging.getLogger(__name__)


# pylint: disable=unused-argument
def _raise_or_return_json(self: Any, response: HttpResponse) -> dict:
    """
    Raise HTTPError before converting response to json

    :param response: Request response object
    """
    response.raise_for_status()

    try:
        json_value = response.json()
    except ValueError:
        return response.content
    return json_value


# pylint: disable=too-many-instance-attributes
class ZammadChatAPI:
    """
    Class providing an API for Zammad used in the context of user chats.

    :param url: The region's Zammad URL
    :param http_token: The region's client secret
    """

    def __init__(self, region: Region):
        self.client = ZammadAPI(
            url=f"{region.zammad_url}/api/v1/", http_token=region.zammad_access_token
        )

        # Patch the relevant methods to allow us to capture error response codes
        self.client.ticket.__class__.__base__._raise_or_return_json = (
            _raise_or_return_json
        )
        self.client.ticket_article.__class__.__base__._raise_or_return_json = (
            _raise_or_return_json
        )
        self.client.user.__class__.__base__._raise_or_return_json = (
            _raise_or_return_json
        )

        try:
            self.client_identity = self.client.user.me()["login"]
        except HTTPError:
            self.create_ticket = self.send_message = self.get_messages = (  # type: ignore[assignment]
                self.get_attachment  # type: ignore[method-assign]
            ) = lambda *_: {
                "status": 500,
                "error": "An error occurred while attempting to connect to the chat server.",
            }
            return

        self.ticket_group = settings.USER_CHAT_TICKET_GROUP
        self.responsible_handlers = region.zammad_chat_handlers

    @staticmethod
    def _attempt_call(call: Callable, *args: Any, **kwargs: Any) -> Any:
        try:
            return call(*args, **kwargs)
        except HTTPError as err:
            logger.warning(
                "A HTTP error with status %s occurred: %s",
                err.response.status_code,
                err.response.text,
            )
            return err.response.json() | {"status": err.response.status_code}

    def _parse_response(self, response: dict | list[dict]) -> dict | list[dict]:
        if isinstance(response, list):
            return [self._parse_response(item) for item in response]  # type: ignore[misc]

        if author := response.get("sender"):
            response["user_is_author"] = author == "Customer"
        keys_to_keep = [
            "status",
            "error",
            "id",
            "body",
            "user_is_author",
            "attachments",
        ]

        return {key: response[key] for key in keys_to_keep if key in response}

    # pylint: disable=method-hidden
    def create_ticket(self, device_id: str, language_slug: str) -> dict:
        """
        Create a new ticket (i.e. initialize a new chat conversation) and
        automatically subscribe the responsible Zammad users

        :param device_id: ID of the user requesting a new chat
        :param language_slug: user's language
        """
        responsible_handlers = [
            user["id"]
            for user in self.client.user.all()
            if user["email"] and user["email"] in self.responsible_handlers
        ]
        params = {
            "title": f"[Integreat Chat] [{language_slug.upper()}] {device_id}",
            "group": self.ticket_group,
            "customer": self.client_identity,
            "mentions": responsible_handlers,
        }
        return self._parse_response(  # type: ignore[return-value]
            self._attempt_call(self.client.ticket.create, params=params)
        )

    @staticmethod
    def _transform_attachment(
        chat: UserChat, article_id: int, attachment: dict
    ) -> dict:
        return {
            "filename": attachment.get("filename", ""),
            "size": attachment.get("size", ""),
            "Content-Type": attachment.get("preferences", {}).get("Content-Type", ""),
            "id": AttachmentMap.objects.get_or_create(
                user_chat=chat,
                article_id=article_id,
                attachment_id=attachment["id"],
            )[0].random_hash,
        }

    # pylint: disable=method-hidden
    def get_messages(self, chat: UserChat) -> dict[str, dict | list[dict]]:
        """
        Get all messages for a given ticket

        :param chat: UserChat instance for the relevant Zammad ticket
        """
        response = self._parse_response(
            self._attempt_call(self.client.ticket.articles, chat.zammad_id)
        )

        for message in response:
            if "attachments" in message:
                message["attachments"] = [
                    self._transform_attachment(chat, message["id"], attachment)
                    for attachment in message["attachments"]
                ]

        return {"messages": response}

    # pylint: disable=method-hidden
    def send_message(self, chat_id: int, message: str) -> dict:
        """
        Post a new message to the given ticket
        """
        params = {
            "ticket_id": chat_id,
            "body": message,
            "type": "chat",
            "internal": False,
            "sender": "Customer",
        }
        return self._parse_response(  # type: ignore[return-value]
            self._attempt_call(self.client.ticket_article.create, params=params)
        )

    # pylint: disable=method-hidden
    def get_attachment(self, attachment_map: AttachmentMap) -> bytes | dict:
        """
        Get the (binary) attachment file from Zammad.

        :param attachment_map: the object containing the IDs Zammad requires to identify attachments
        :return: the binary object file or a dict containing an error message
        """
        return self._attempt_call(
            self.client.ticket_article_attachment.download,
            attachment_map.attachment_id,
            attachment_map.article_id,
            attachment_map.user_chat.zammad_id,
        )
