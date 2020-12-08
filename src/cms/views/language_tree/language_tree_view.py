from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...models import Region
from .language_tree_mixin import LanguageTreeMixin


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
# pylint: disable=too-many-ancestors
class LanguageTreeView(PermissionRequiredMixin, TemplateView, LanguageTreeMixin):
    """
    View for rendering the language tree view.
    This view is available in regions.
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_language_tree"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "language_tree/language_tree.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "language_tree"}

    def get(self, request, *args, **kwargs):
        """
        Render language tree

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        region = Region.get_current_region(request)
        language_tree = region.language_tree_nodes.all()
        context = self.get_context_data(**kwargs)
        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                **context,
                "language_tree": language_tree,
            },
        )
