from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import ContactForm
from .contact_context_mixin import ContactContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse


@method_decorator(permission_required("cms.view_contact"), name="dispatch")
@method_decorator(permission_required("cms.change_contact"), name="post")
class ContactFormAjaxView(TemplateView, ContactContextMixin):
    """
    View for the ajax contact widget
    """

    template = "ajax_contact_form/_contact_form_widget.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""Render a contact form widget template

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The html template of a POI form
        """
        contact_form = ContactForm(
            additional_instance_attributes={"region": request.region}
        )

        return render(
            request,
            "ajax_contact_form/_contact_form_widget.html",
            {
                **self.get_context_data(**kwargs),
                "contact_form": contact_form,
                "poi_id": kwargs.get(
                    "poi_id",
                ),
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""Add a new POI to the database

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.http.Http404: If no language for the given language slug was found

        :return: A status message, either a success or an error message
        """
        data = request.POST.dict()

        contact_form = ContactForm(
            data=data,
            files=request.FILES,
            instance=None,
            additional_instance_attributes={
                "region": request.region,
            },
        )

        if not contact_form.is_valid():
            return JsonResponse(
                data={
                    "contact_form": contact_form.get_error_messages(),
                }
            )

        contact = contact_form.save()

        return JsonResponse(
            data={
                "success": "Successfully created location",
                "contact_label": contact.label_in_reference_list(),
                "edit_url": contact.backend_edit_link,
            }
        )
