import logging

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from backend.settings import PER_PAGE
from ...forms import ObjectSearchForm
from ...decorators import region_permission_required, permission_required
from ...models import Region
from ...utils.user_utils import search_users

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
@method_decorator(permission_required("cms.view_user"), name="dispatch")
class RegionUserListView(TemplateView):
    """
    View for listing region users
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "users/region/list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "region_users"}

    def get(self, request, *args, **kwargs):
        """
        Render region user list

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
        users = (region.users.select_related("organization")
            .prefetch_related("groups__role")
            .order_by("username"))
        query = None

        search_data = kwargs.get("search_data")
        search_form = ObjectSearchForm(search_data)
        if search_form.is_valid():
            query = search_form.cleaned_data["query"]
            user_keys = search_users(region, query).values("pk")
            users = users.filter(pk__in=user_keys)

        # for consistent pagination querysets should be ordered
        paginator = Paginator(
            users.order_by("username").select_related("organization").prefetch_related("groups__role")
            .order_by("username"), PER_PAGE
        )
        # for consistent pagination querysets should be ordered
        paginator = Paginator(users, PER_PAGE)
        chunk = request.GET.get("page")
        user_chunk = paginator.get_page(chunk)
        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "users": user_chunk,
                "region_slug": region.slug,
                "search_query": query,
            },
        )

    def post(self, request, *args, **kwargs):
        """
        Apply the query and filter the rendered users

        :param request: The current request
        :type request: ~django.http.HttpResponse
        :param args: The supplied arguments
        :type args: list
        :param kwargs: The supplied keyword arguments
        :type kwargs: dict
        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        return self.get(request, *args, **kwargs, search_data=request.POST)
