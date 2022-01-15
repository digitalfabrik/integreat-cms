import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import region_permission_required, permission_required
from .language_tree_context_mixin import LanguageTreeContextMixin

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
@method_decorator(permission_required("cms.view_languagetreenode"), name="dispatch")
class LanguageTreeView(TemplateView, LanguageTreeContextMixin):
    """
    View for rendering the language tree view.
    This view is available in regions.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "language_tree/language_tree.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "language_tree"}

    def get(self, request, *args, **kwargs):
        r"""
        Render language tree

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        region = request.region
        context = self.get_context_data(**kwargs)
        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                **context,
                "language_tree": region.language_tree,
            },
        )
