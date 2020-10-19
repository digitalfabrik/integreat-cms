"""
This module is for showing the list of available languages in the network administration back end.
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import staff_required
from ...models import Language


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class LanguageListView(PermissionRequiredMixin, TemplateView):
    """
    Handles viewing the list of available languages
    """

    permission_required = "cms.manage_languages"
    raise_exception = True

    template_name = "languages/language_list.html"
    base_context = {"current_menu_item": "languages"}

    def get(self, request, *args, **kwargs):
        """
        Handle HTTP GET to show list of available languages

        :param request: The current request
        :type request: django.http.HttpResponse

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        return render(
            request,
            self.template_name,
            {**self.base_context, "languages": Language.objects.all()},
        )
