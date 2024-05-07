from django.apps import apps
from django.core import serializers

# Defines that models that may be imported as keys and overwrites for each model as values
MODEL_CONFIGURATION: dict[tuple[str, str], dict] = {
    ("cms", "Language"): {},
    ("cms", "LanguageTreeNode"): {},
    ("cms", "Page"): {},
    ("cms", "PageTranslation"): {"creator": None},
    ("cms", "Region"): {},
}


def dump_database() -> str:
    """
    Creates a database dump including all objects related to the given models.
    :return: A database dump of these objects serialized
    """
    objects = []
    for (app_name, model_name), overwrites in MODEL_CONFIGURATION.items():
        model = apps.get_model(app_name, model_name)
        for obj in model.objects.all():
            for attribute_name, new_value in overwrites.items():
                if hasattr(obj, attribute_name):
                    setattr(obj, attribute_name, new_value)

            objects.append(obj)

    data = serializers.serialize("json", objects)
    return data
