from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.generic import TemplateView

from ...forms import PlaceForm, PlaceTranslationForm
from ...models import Language
from ...models.places.place import get_default_opening_hours
from ..utils.contact_utils import generate_primary_contact_from_place
from .place_context_mixin import PlaceContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse


class PlaceFormAjaxView(TemplateView, PlaceContextMixin):
    """
    View for the ajax place widget
    """

    #: Template for ajax place widget
    template = "ajax_place_form/_place_form_widget.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""Render a place form widget template

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The html template of a place form
        """
        place_form = PlaceForm(
            additional_instance_attributes={"region": request.region}
        )
        place_title = kwargs.get("place_title")
        place_translation_form = PlaceTranslationForm(data={"title": place_title})

        return render(
            request,
            "ajax_place_form/_place_form_widget.html",
            {
                **self.get_context_data(**kwargs),
                "place_form": place_form,
                "place_translation_form": place_translation_form,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""Add a new place to the database

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.http.Http404: If no language for the given language slug was found

        :return: A status message, either a success or an error message
        """

        region = request.region
        language_slug = kwargs.get("language_slug")
        language = get_object_or_404(Language, slug=language_slug)

        data = request.POST.dict()
        data["opening_hours"] = get_default_opening_hours()

        place_form = PlaceForm(
            data=data,
            files=request.FILES,
            instance=None,
            additional_instance_attributes={
                "region": region,
            },
        )

        with transaction.atomic():
            if not place_form.is_valid():
                return JsonResponse(
                    data={
                        "success": False,
                    },
                )
            place = place_form.save()

            place_translation_form = PlaceTranslationForm(
                data=request.POST,
                instance=None,
                additional_instance_attributes={
                    "creator": request.user,
                    "language": language,
                    "place": place,
                },
                changed_by_user=request.user,
            )

            if not place_translation_form.is_valid():
                return JsonResponse(
                    data={
                        "success": False,
                    },
                )

            phone_number = place_form.data.get("primary_phone_number")
            email = place_form.data.get("primary_email")
            website = place_form.data.get("primary_website")

            place_translation_form.instance.place = place
            place_translation = place_translation_form.save()

            generate_primary_contact_from_place(
                website,
                phone_number,
                email,
                place,
                language,
                region,
                place_translation.title,
            )

        return JsonResponse(
            data={
                "success": True,
                "place_address_container": render_to_string(
                    "ajax_place_form/_place_address_container.html",
                    {"place": place_translation_form.instance.place},
                ),
                "place_id": place_translation_form.instance.place.id,
            }
        )
