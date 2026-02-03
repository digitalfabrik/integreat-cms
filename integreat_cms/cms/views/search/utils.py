from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import apps

if TYPE_CHECKING:
    from django.db.models import Model

#: Content types that are not language-specific
CONTENT_TYPES: list[str] = [
    "contact",
    "feedback",
    "language",
    "mediafile",
    "organization",
    "region",
    "user",
]

#: Content types that have language-specific translations
TRANSLATION_CONTENT_TYPES: list[str] = ["event", "page", "poi", "pushnotification"]


def get_model_cls_from_object_type(
    object_type: str,
    language_slug: str | None,
) -> type[Model]:
    """
    Get the Django model class for a given object type.

    For translation content types (event, poi, pushnotification), returns the
    translation model (e.g., EventTranslation). For "page", returns the Page model
    directly since pages use a different translation pattern.

    :param object_type: The type of object (e.g., "page", "event", "contact")
    :param language_slug: The language slug, required for translation content types
    :raises AttributeError: If the object type is unknown or language_slug is missing for translation types
    :return: The Django model class
    """
    if object_type not in CONTENT_TYPES + TRANSLATION_CONTENT_TYPES:
        raise AttributeError(f"Unexpected object type: {object_type}")

    if object_type in TRANSLATION_CONTENT_TYPES and not language_slug:
        raise AttributeError(
            f"Language slug is required for object type: {object_type}"
        )

    if object_type in CONTENT_TYPES or object_type == "page":
        return apps.get_model("cms", object_type)

    translation_model_name = f"{object_type}translation"
    return apps.get_model("cms", translation_model_name)
