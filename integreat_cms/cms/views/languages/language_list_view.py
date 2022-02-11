import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import staff_required, permission_required
from ...models import Language

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
@method_decorator(permission_required("cms.view_language"), name="dispatch")
class LanguageListView(TemplateView):
    """
    This view shows the list of available languages in the network administration back end.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "languages/language_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "languages"}

    def get(self, request, *args, **kwargs):
        r"""
        Handle HTTP GET to show list of available languages

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        languages = Language.objects.all().prefetch_related("language_tree_nodes")
        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        # for consistent pagination querysets should be ordered
        paginator = Paginator(languages.order_by("slug"), chunk_size)
        chunk = request.GET.get("page")
        language_chunk = paginator.get_page(chunk)
        return render(
            request,
            self.template_name,
            {**self.get_context_data(**kwargs), "languages": language_chunk},
        )
