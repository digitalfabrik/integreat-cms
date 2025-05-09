from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import ObjectSearchForm
from ...models import Contact
from .contact_context_mixin import ContactContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse


@method_decorator(permission_required("cms.view_contact"), name="dispatch")
class ContactListView(TemplateView, ContactContextMixin):
    """
    View for listing contacts
    """

    template_name = "contacts/contact_list.html"
    archived = False

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render contact list

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        region = request.region
        query = None

        contacts = Contact.objects.filter(
            location__region=region,
            archived=self.archived,
        ).select_related("location")

        archived_count = Contact.objects.filter(
            location__region=region,
            archived=True,
        ).count()

        search_data = kwargs.get("search_data")
        search_form = ObjectSearchForm(search_data)
        if search_form.is_valid():
            query = search_form.cleaned_data["query"]
            contact_keys = Contact.search_for_query(region, query).values("pk")
            contacts = contacts.filter(pk__in=contact_keys)

        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        paginator = Paginator(
            contacts,
            chunk_size,
        )
        chunk = request.GET.get("page")
        contact_chunk = paginator.get_page(chunk)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "is_archive": self.archived,
                "region_slug": region.slug,
                "contacts": contact_chunk,
                "archived_count": archived_count,
                "current_menu_item": "contacts",
                "search_query": query,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Apply the query and filter the rendered contacts
        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        return self.get(request, *args, **kwargs, search_data=request.POST)
