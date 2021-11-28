import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import staff_required, permission_required
from ...forms import LanguageForm
from ...models import Language

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
@method_decorator(permission_required("cms.view_language"), name="dispatch")
@method_decorator(permission_required("cms.change_language"), name="post")
class LanguageView(TemplateView):
    """
    This view shows and editing languages in the network administration back end.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "languages/language_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "languages"}

    def get(self, request, *args, **kwargs):
        r"""
        Handle HTTP GET to show form for a language

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        language_instance = Language.objects.filter(
            slug=kwargs.get("language_slug")
        ).first()
        form = LanguageForm(instance=language_instance)
        return render(request, self.template_name, {"form": form, **self.base_context})

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        r"""
        Handle HTTP to save and show form for a language

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        language_instance = Language.objects.filter(
            slug=kwargs.get("language_slug")
        ).first()
        form = LanguageForm(data=request.POST, instance=language_instance)

        if not form.is_valid():
            # Add error messages
            form.add_error_messages(request)
        elif not form.has_changed():
            # Add "no changes" messages
            messages.info(request, _("No changes made"))
        else:
            # Save form
            form.save()
            # Add the success message and redirect to the edit page
            if not language_instance:
                messages.success(
                    request,
                    _('Language "{}" was successfully created').format(form.instance),
                )
                return redirect("edit_language", language_slug=form.instance.slug)
            # Add the success message
            messages.success(
                request, _('Language "{}" was successfully saved').format(form.instance)
            )

        return render(request, self.template_name, {"form": form, **self.base_context})
