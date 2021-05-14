from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from backend.settings import PER_PAGE
from ...decorators import staff_required
from ...models import Language


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class LanguageListView(PermissionRequiredMixin, TemplateView):
    """
    This view shows the list of available languages in the network administration back end.
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_languages"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "languages/language_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "languages"}

    def get(self, request, *args, **kwargs):
        """
        Handle HTTP GET to show list of available languages

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        languages = Language.objects.all()
        # for consistent pagination querysets should be ordered
        paginator = Paginator(languages.order_by("slug"), PER_PAGE)
        chunk = request.GET.get("page")
        language_chunk = paginator.get_page(chunk)
        return render(
            request,
            self.template_name,
            {**self.base_context, "languages": language_chunk},
        )
