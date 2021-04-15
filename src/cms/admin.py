"""
File routing to the admin region
"""
from django.apps import apps
from django.conf import settings
from django.contrib import admin


if settings.DEBUG:
    for model in apps.get_app_config("cms").get_models():
        admin.site.register(model)
