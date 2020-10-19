"""
Module for viewing the LanguageTree. This view is available in regions.
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...models import Region


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class LanguageTreeView(PermissionRequiredMixin, TemplateView):
    """
    Class for handling the language tree view
    """

    permission_required = "cms.manage_language_tree"
    raise_exception = True

    template_name = "language_tree/language_tree.html"
    base_context = {"current_menu_item": "language_tree"}

    def get(self, request, *args, **kwargs):
        """
        Handle HTTP GET requests to show the full language tree

        :param request: The current request
        :type request: django.http.HttpResponse

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        region = Region.get_current_region(request)
        language_tree = region.language_tree_nodes.all()

        return render(
            request,
            self.template_name,
            {**self.base_context, "language_tree": language_tree},
        )
