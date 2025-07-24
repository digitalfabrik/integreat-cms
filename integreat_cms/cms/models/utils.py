from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from lxml.html import tostring

if TYPE_CHECKING:
    from typing import Any, Literal

    from ...models.abstract_content_translation import AbstractContentTranslation


def get_default_opening_hours() -> list[dict[str, Any]]:
    """
    Return the default opening hours

    :return: The default opening hours
    """
    return [
        {"allDay": False, "closed": True, "appointmentOnly": False, "timeSlots": []}
        for _ in range(7)
    ]


def format_object_translation(
    object_translation: AbstractContentTranslation,
    typ: Literal["page", "event", "poi"],
    target_language_slug: str,
) -> dict:
    """
    Formats the [poi/event/page]-translation as json

    :param object_translation: A translation object which has a title and a permalink
    :param typ: The type of this object
    :param target_language_slug: The slug that the object translation should ideally have
    :return: A dictionary with the title, path, url and type of the translation object
    """
    if object_translation.language.slug != target_language_slug:
        object_translation = object_translation.foreign_object.get_public_translation(
            target_language_slug,
        )
    if isinstance(object_translation.link_title, str):
        html_title = object_translation.link_title
        text_title = object_translation.link_title
    else:
        html_title = tostring(object_translation.link_title).decode("utf-8")
        text_title = (
            object_translation.link_title.text_content()
            + object_translation.link_title.tail
        )
    return {
        "path": object_translation.path(),
        "title": text_title,
        "html_title": html_title,
        "url": f"{settings.WEBAPP_URL}{object_translation.get_absolute_url()}",
        "type": typ,
    }
