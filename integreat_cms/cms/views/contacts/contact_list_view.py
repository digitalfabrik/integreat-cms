from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms.contacts.contact_search_form import ContactSearchForm
from ...models import Contact
from ..mixins import FilterSortMixin, PaginationMixin
from .contact_context_mixin import ContactContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse


@method_decorator(permission_required("cms.view_contact"), name="dispatch")
class ContactListView(
    TemplateView, ContactContextMixin, FilterSortMixin, PaginationMixin
):
    """
    View for listing contacts
    """

    template_name = "contacts/contact_list.html"
    archived = False
    filter_form_class = ContactSearchForm

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

        if not region.contacts_enabled:
            return self.redirect_to_dashboard(request)

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

        contacts = self.get_filtered_sorted_queryset(contacts)
        contact_chunk = self.paginate_queryset(contacts)

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

    def redirect_to_dashboard(self, request: HttpRequest) -> None:
        """
        This function redirects to the dashboard if contacts are not enabled.

        :param request: The current request

        :return: template of region dashboard
        """
        messages.info(request, _("Contacts are not enabled for this region."))
        return redirect(
            "dashboard",
            **{
                "region_slug": request.region.slug,
            },
        )
