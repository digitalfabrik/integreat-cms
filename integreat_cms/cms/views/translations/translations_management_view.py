import logging

from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db import transaction
from django.utils.translation import gettext as _

from ...forms import TranslationsManagementForm

from ...decorators import permission_required

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.manage_translations"), name="dispatch")
class TranslationsManagementView(TemplateView):
    """
    View for showing the machine translations management options
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "translations/translations_management.html"

    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "translations_management"}

    def get(self, request, *args, **kwargs):
        r"""
        Render translations management interface

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        form = TranslationsManagementForm(instance=request.region)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "form": form,
            },
        )

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        r"""
        Submit :class:`~integreat_cms.cms.forms.translations.translations_management_form.TranslationsManagementForm` objects.

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        form = TranslationsManagementForm(
            data=request.POST,
            instance=request.region,
        )

        if not form.is_valid():
            # Add error messages
            form.add_error_messages(request)
            return render(
                request,
                self.template_name,
                {
                    **self.get_context_data(**kwargs),
                    "form": form,
                },
            )

        # Save the machine translation settings
        form.save()

        messages.success(
            request,
            _("Automatic translation settings were saved successfully."),
        )

        return redirect(
            "translations_management",
            **{
                "region_slug": request.region.slug,
            },
        )
