from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
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

        if not region.default_language:
            return self.redirect_to_language_tree(request)

        pois = region.pois.filter(
            translations__language=region.default_language,
        ).distinct()

        if not pois:
            return self.redirect_to_poi_list(request)

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

    def redirect_to_language_tree(self, request: HttpRequest) -> None:
        """
        This function redirects to the language tree if there is no default language.

        :param request: The current request

        :return: template of language tree
        """
        region = request.region
        messages.error(
            request,
            _("Please create at least one language node before creating contacts."),
        )
        return redirect(
            "languagetreenodes",
            **{
                "region_slug": region.slug,
            },
        )

    def redirect_to_poi_list(self, request: HttpRequest) -> None:
        """
        This function redirects to the poi list if there is no default language.

        :param request: The current request

        :return: template of poi list
        """
        region = request.region
        messages.error(
            request,
            _("Please create at least one location before creating contacts."),
        )
        return redirect(
            "pois",
            **{
                "region_slug": region.slug,
            },
        )
