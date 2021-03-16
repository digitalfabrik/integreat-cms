from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import staff_required
from ...forms import LanguageForm
from ...models import Language


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class LanguageView(PermissionRequiredMixin, TemplateView):
    """
    This view shows and editing languages in the network administration back end.
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_languages"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "languages/language_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "languages"}

    def get(self, request, *args, **kwargs):
        """
        Handle HTTP GET to show form for a language

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        language = Language.objects.filter(slug=kwargs.get("language_slug")).first()
        form = LanguageForm(instance=language)
        return render(request, self.template_name, {"form": form, **self.base_context})

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        """
        Handle HTTP to save and show form for a language

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        language_slug = kwargs.get("language_slug")
        language = Language.objects.filter(slug=language_slug).first()
        form = LanguageForm(request.POST, instance=language)
        if form.is_valid():
            form.save()
            if language_slug:
                messages.success(request, _("Language was successfully saved"))
            else:
                messages.success(request, _("Language was successfully created"))
        else:
            # TODO: error handling
            # TODO: improve messages
            messages.error(request, _("An error has occurred."))

        return render(request, self.template_name, {"form": form, **self.base_context})
