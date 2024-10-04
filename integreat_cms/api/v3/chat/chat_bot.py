"""
Wrapper for the Chat Bot / LLM API
"""

import requests
from django.conf import settings

from ....cms.models import Region
from ....cms.utils.content_translation_utils import get_public_translation_for_link


class ChatBot:
    """
    API Wrapper for the LLM / Chat Bot
    """

    def __init__(self, hostname: str = "igchat-inference.tuerantuer.org"):
        self.hostname = hostname

    def automatic_answer(self, message: str, region: Region, language_slug: str) -> str:
        """
        Get automatic answer to question
        """
        url = f"https://{self.hostname}/chatanswers/extract_answer/"
        body = {"message": message, "language": language_slug, "region": region.slug}
        r = requests.post(url, json=body, timeout=30)
        return self.format_message(r.json())

    def format_message(self, response: dict) -> str:
        """
        Transform JSON into readable message
        """
        if "answer" not in response or not response["answer"]:
            return ""
        if "sources" not in response or not response["sources"]:
            return response["answer"]
        sources = "".join(
            [
                f"<li><a href='{settings.WEBAPP_URL}{path}'>{title}</a></li>"
                for path in response["sources"]
                if (
                    title := get_public_translation_for_link(settings.WEBAPP_URL + path)
                )
            ]
        )
        return f"{response['answer']}\n<ul>{sources}</ul>"

    def automatic_translation(
        self, message: str, source_lang_slug: str, target_lang_slug: str
    ) -> str:
        """
        Use LLM to translate message
        """
        url = f"https://{self.hostname}/chatanswers/translate_message/"
        body = {
            "message": message,
            "source_language": source_lang_slug,
            "target_language": target_lang_slug,
        }
        response = requests.post(url, json=body, timeout=30).json()
        if "status" in response and response["status"] == "success":
            return response["translation"]
        return ""
