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

from integreat_cms.cms.models import AttachmentMap, Region, UserChat

logger = logging.getLogger(__name__)


AUTO_ANSWER_STRING = "automatically generated message"


def _raise_or_return_json(
    self: Any, response: HttpResponse  # pylint: disable=unused-argument
) -> dict:
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


class ZammadChatAPI:
    # pylint: disable=too-many-instance-attributes
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
            response["user_is_author"] = (
                author == "Customer" and response.get("subject") != AUTO_ANSWER_STRING
            )
        response["automatic_answer"] = response.get("subject") == AUTO_ANSWER_STRING
        keys_to_keep = [
            "status",
            "error",
            "id",
            "body",
            "user_is_author",
            "attachments",
            "automatic_answer",
        ]

        return {key: response[key] for key in keys_to_keep if key in response}

    def create_ticket(self, device_id: str, language_slug: str) -> dict:
        # pylint: disable=method-hidden
        """
        Create a new ticket (i.e. initialize a new chat conversation)

        :param device_id: ID of the user requesting a new chat
        :param language_slug: user's language
        """
        params = {
            "title": f"[Integreat Chat] [{language_slug.upper()}] {device_id}",
            "group": self.ticket_group,
            "customer": self.client_identity,
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

    def get_messages(self, chat: UserChat) -> dict[str, dict | list[dict]]:
        # pylint: disable=method-hidden
        """
        Get all non-internal messages for a given ticket

        :param chat: UserChat instance for the relevant Zammad ticket
        """
        raw_response = self._attempt_call(self.client.ticket.articles, chat.zammad_id)
        if not isinstance(raw_response, list):
            return self._parse_response(raw_response)  # type: ignore[return-value]

        response = self._parse_response(
            [article for article in raw_response if not article.get("internal")]
        )
        for message in response:
            if "attachments" in message:
                message["attachments"] = [
                    self._transform_attachment(chat, message["id"], attachment)
                    for attachment in message["attachments"]
                ]

        return {"messages": response}

    def send_message(
        self,
        chat_id: int,
        message: str,
        internal: bool = False,
        automatic_message: bool = False,
    ) -> dict:
        # pylint: disable=method-hidden
        """
        Post a new message to the given ticket

        param chat_id: Zammad ID of the chat
        param message: The message body
        param internal: keep the message internal in Zammad (do not show to user)
        param automatic_message: sets title to "automatically generated message"
        return: dict with Zammad article data
        """
        params = {
            "ticket_id": chat_id,
            "body": message,
            "type": "web",
            "content_type": "text/html",
            "internal": internal,
            "subject": (
                "automatically generated message"
                if automatic_message
                else "app user message"
            ),
            "sender": "Customer" if not automatic_message else "Agent",
        }
        return self._parse_response(  # type: ignore[return-value]
            self._attempt_call(self.client.ticket_article.create, params=params)
        )

    def get_attachment(self, attachment_map: AttachmentMap) -> bytes | dict:
        # pylint: disable=method-hidden
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
