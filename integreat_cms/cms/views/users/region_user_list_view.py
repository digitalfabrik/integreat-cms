import logging

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...forms import ObjectSearchForm
from ...decorators import permission_required
from ...utils.user_utils import search_users

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_user"), name="dispatch")
class RegionUserListView(TemplateView):
    """
    View for listing region users
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "users/region_user_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "region_users"}

    def get(self, request, *args, **kwargs):
        r"""
        Render region user list

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = request.region

        users = (
            region.region_users.select_related("organization")
            .prefetch_related("groups__role")
            .order_by("username")
        )
        query = None

        search_data = kwargs.get("search_data")
        search_form = ObjectSearchForm(search_data)
        if search_form.is_valid():
            query = search_form.cleaned_data["query"]
            user_keys = search_users(region, query).values("pk")
            users = users.filter(pk__in=user_keys)

        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        # for consistent pagination querysets should be ordered
        paginator = Paginator(users, chunk_size)
        chunk = request.GET.get("page")
        user_chunk = paginator.get_page(chunk)
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "users": user_chunk,
                "region_slug": region.slug,
                "search_query": query,
            },
        )

    def post(self, request, *args, **kwargs):
        r"""
        Apply the query and filter the rendered users

        :param request: The current request
        :type request: ~django.http.HttpRequest
        :param \*args: The supplied arguments
        :type \*args: list
        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        return self.get(request, *args, **kwargs, search_data=request.POST)
