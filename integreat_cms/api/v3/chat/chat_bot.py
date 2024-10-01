"""
Wrapper for the Chat Bot / LLM API
"""

import requests
from django.conf import settings

from ....cms.models import Region


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
        if not response["answer"]:
            return ""
        sources = "".join(
            [
                f"<li><a href='{settings.WEBAPP_URL}{path}'>{path}</a></li>"
                for path in response["sources"]
            ]
        )
        return f"{response['answer']}\n<ul>{sources}</ul>"

    def automatic_translation(
        self, message: str, source_lang_slug: str, target_lang_slug: str
    ) -> str:
        """
        Use LLM to translate message
        """
        raise NotImplementedError
