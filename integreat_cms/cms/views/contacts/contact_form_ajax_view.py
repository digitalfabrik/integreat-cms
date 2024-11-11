from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView

from ...forms import ContactForm
from ...models import Language
from ...models.contact import contact
from .contact_context_mixin import ContactContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse


class ContactFormAjaxView(TemplateView, ContactContextMixin):
    """
    View for the ajax contact widget
    """

    #: Template for ajax POI widget
    template = "ajax_contact_form/contact_box.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""Render a contact form widget template

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The html template of a POI form
        """
        contact_form = ContactForm()

        return render(
            request,
            "ajax_contact_form/contact_box.html",
            {
                **self.get_context_data(**kwargs),
                "contact_form": contact_form,
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

        region = request.region
        language_slug = kwargs.get("language_slug")
        language = get_object_or_404(Language, slug=language_slug)

        contact_instance = contact.objects.filter(id=None).first()

        data = request.POST.dict()

        contact_form = ContactForm(
            data=data,
            files=request.FILES,
            instance=contact_instance,
            additional_instance_attributes={
                "region": region,
            },
        )

        if not contact_form.is_valid():
            return JsonResponse(
                data={
                    "contact_form": contact_form.get_error_messages(),
                }
            )

        contact_form = contact_form.save()

        return JsonResponse(
            data={
                "success": "Successfully created location",
                "id": contact_form.instance.id,
            }
        )
