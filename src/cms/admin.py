"""
File routing to the admin region
"""
from django.apps import apps
from django.contrib import admin


for model in apps.get_app_config("cms").get_models():
    admin.site.register(model)
