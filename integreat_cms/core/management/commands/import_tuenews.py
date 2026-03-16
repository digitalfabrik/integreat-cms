import logging
from typing import Any

import requests
from django.core.management.base import BaseCommand

from ....cms.models import NewsItem, NewsLanguage
from ....cms.utils.tue_news_utils import clean_html

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to fetch Tü News posts
    """

    help = "Get news from tuenews.de"

    def handle(self, *args: Any, **options: Any) -> None:
        languages = NewsLanguage.objects.filter(wpcategory__isnull=False)
        for language in languages:
            posts = requests.get(
                f"http://tuenews.de/wp-json/wp/v2/posts/?lang={language.code}",
                timeout=10,
            ).json()

            logger.info(
                "Got %s posts.",
                len(posts),
            )

            for post in posts:
                if not post["acf"]["integreat"]:
                    continue

                if NewsItem.objects.filter(wppostid=post["id"]):
                    logger.info(
                        "News %s already exists.",
                        post["id"],
                    )
                    continue

                newsitem = NewsItem(
                    title=post["title"]["rendered"],
                    content=clean_html(post["content"]["rendered"]),
                    enewsno=post["acf"]["tun_nummer"],
                    pub_date=post["date"] + "+00:00",
                    language=language,
                    wppostid=post["id"],
                )
                newsitem.save()
                logger.info("Saving %s", newsitem)
