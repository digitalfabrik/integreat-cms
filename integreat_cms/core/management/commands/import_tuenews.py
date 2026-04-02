import logging
from io import StringIO
from typing import Any

import requests
from django.core.cache import cache
from django.core.management.base import BaseCommand
from lxml import etree

from ....cms.models import Language

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to fetch Tü News posts
    """

    help = "Get news from tuenews.de"

    def clean_html(self, html_string: str) -> str:
        """
        Remove unnecessary HTML elements.
        """
        root = etree.parse(  # noqa: S320
            StringIO("<main>" + html_string + "</main>"), etree.HTMLParser()
        )
        xpath_pvc = '//*[contains(@class, "pvc_")]'

        for pvc in root.xpath(xpath_pvc):
            pvc.getparent().remove(pvc)
        main = root.xpath("body/main")[0]

        return etree.tostring(main, pretty_print=True).decode("utf-8")

    def transform_post(self, post: Any) -> dict[str, Any]:
        """
        Transforms a post of Tü News so it can be used by the news endpoint directly
        """
        return {
            "id": post["id"],
            "title": post["title"]["rendered"],
            "message": self.clean_html(post["content"]["rendered"]),
            "timestamp": post["date"] + "+00:00",  # deprecated field in the future
            "last_updated": post["date"] + "+00:00",
            "display_date": post["date"] + "+00:00",
            "channel": None,
            "available_languages": None,
            "source": "tuenews",
            "link": post["link"],
        }

    def handle(self, *args: Any, **options: Any) -> None:
        r"""
        Imports posts from Tü News and save in the cache

        :param \*args: The supplied arguments
        :param \**options: The supplied keyword options
        """

        for language in Language.objects.all():
            response = requests.get(
                f"http://tuenews.de/wp-json/wp/v2/posts/?lang={language.slug}",
                timeout=10,
            )

            if response.status_code != 200:
                continue

            posts = response.json()

            logger.info(
                "Got %s posts.",
                len(posts),
            )

            news = []

            for post in posts:
                if not post["acf"]["integreat"]:
                    continue

                news.append(self.transform_post(post))

            cache.delete(f"tuenews:{language.slug}")
            cache.set(f"tuenews:{language.slug}", news, timeout=60 * 60 * 24)

            logger.info("Saving %s news in %s", len(news), language)
