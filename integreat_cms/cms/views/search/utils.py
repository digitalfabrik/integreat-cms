from django.apps import apps
from django.db.models import Model


CONTENT_TYPES = [
    "contact",
    "feedback",
    "language",
    "mediafile",
    "organization",
    "region",
    "user",
]
TRANSLATION_CONTENT_TYPES = ["event", "page", "poi", "pushnotification"]


def get_model_cls_from_object_type(object_type: str, language_slug: str) -> type[Model]:
    """
    Get model class from object type and language slug
    """
    if object_type not in CONTENT_TYPES + TRANSLATION_CONTENT_TYPES:
        raise AttributeError(f"Unexpected object type: {object_type}")

    if object_type in TRANSLATION_CONTENT_TYPES and not language_slug:
        raise AttributeError("Language slug is not provided")

    if object_type in CONTENT_TYPES or object_type == "page":
        return apps.get_model("cms", object_type)
    else:
        translation_object_type = f"{object_type}translation"
        return apps.get_model("cms", translation_object_type)
