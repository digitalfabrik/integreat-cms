import logging

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...forms import ObjectSearchForm
from ...decorators import permission_required
from ...models import Region

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_region"), name="dispatch")
class RegionListView(TemplateView):
    """
    View for listing regions
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "regions/region_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "regions"}

    def get(self, request, *args, **kwargs):
        r"""
        Render region list

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        regions = Region.objects.all()
        query = None

        search_data = kwargs.get("search_data")
        search_form = ObjectSearchForm(search_data)
        if search_form.is_valid():
            query = search_form.cleaned_data["query"]
            region_keys = Region.search(query).values("pk")
            regions = regions.filter(pk__in=region_keys)

        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        paginator = Paginator(regions, chunk_size)
        chunk = request.GET.get("page")
        region_chunk = paginator.get_page(chunk)
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "regions": region_chunk,
                "search_query": query,
            },
        )

    def post(self, request, *args, **kwargs):
        r"""
        Apply the query and filter the rendered regions

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        return self.get(request, *args, **kwargs, search_data=request.POST)
