"""
Debug lists and forms for all models
"""
from django.apps import apps
from django.conf import settings
from django.contrib import admin

from treebeard.admin import TreeAdmin
from treebeard.ns_tree import NS_Node
from treebeard.forms import movenodeform_factory


if settings.DEBUG:
    for model in apps.get_app_config("cms").get_models():
        if issubclass(model, NS_Node):

            class ModelTreeAdmin(TreeAdmin):
                """
                A custom model class to allow drag & drop in Django admin
                """

                # pylint: disable=undefined-loop-variable
                #: The form is dynamically generated via :func:`treebeard.forms.movenodeform_factory`
                form = movenodeform_factory(model)
                # Filters in the right sidebar of the lists
                list_filter = ("region",)
                #: Which fields are displayed as columns in the lists
                list_display = ("__str__", "region")
                #: How lists of objects should be ordered
                ordering = ("region",)

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
