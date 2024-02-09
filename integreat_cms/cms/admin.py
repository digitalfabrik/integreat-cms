"""
Debug lists and forms for all models
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from treebeard.ns_tree import NS_Node

if TYPE_CHECKING:
    from django.forms import ModelForm

if settings.DEBUG:
    for model in apps.get_app_config("cms").get_models():
        if issubclass(model, NS_Node):

            class ModelTreeAdmin(TreeAdmin):
                """
                A custom model class to allow drag & drop in Django admin
                """

                #: The form is dynamically generated via :func:`treebeard.forms.movenodeform_factory`
                form: ModelForm = movenodeform_factory(model)
                # Filters in the right sidebar of the lists
                list_filter: tuple[str, ...] = ("region",)
                #: Which fields are displayed as columns in the lists
                list_display: tuple[str, ...] = ("__str__", "region")
                #: How lists of objects should be ordered
                ordering: tuple[str, ...] = ("region",)

            admin.site.register(model, ModelTreeAdmin)
        else:
            admin.site.register(model)
    admin.site.register(apps.get_model("auth", "Permission"))
    for model in apps.get_app_config("admin").get_models():
        admin.site.register(model)
    for model in apps.get_app_config("linkcheck").get_models():
        admin.site.register(model)
    for model in apps.get_app_config("contenttypes").get_models():
        admin.site.register(model)
    for model in apps.get_app_config("sessions").get_models():
        admin.site.register(model)
