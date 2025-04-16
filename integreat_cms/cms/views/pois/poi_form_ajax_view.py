from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.generic import TemplateView

from ...forms import POIForm, POITranslationForm
from ...models import Language
from ...models.pois.poi import get_default_opening_hours
from .poi_context_mixin import POIContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse


class POIFormAjaxView(TemplateView, POIContextMixin):
    """
    View for the ajax POI widget
    """

    #: Template for ajax POI widget
    template = "ajax_poi_form/_poi_form_widget.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""Render a POI form widget template

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The html template of a POI form
        """
        poi_form = POIForm(additional_instance_attributes={"region": request.region})
        poi_title = kwargs.get("poi_title")
        poi_translation_form = POITranslationForm(data={"title": poi_title})

        return render(
            request,
            "ajax_poi_form/_poi_form_widget.html",
            {
                **self.get_context_data(**kwargs),
                "poi_form": poi_form,
                "poi_translation_form": poi_translation_form,
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

        data = request.POST.dict()
        data["opening_hours"] = get_default_opening_hours()

        poi_form = POIForm(
            data=data,
            files=request.FILES,
            instance=None,
            additional_instance_attributes={
                "region": region,
            },
        )

        poi_translation_form = POITranslationForm(
            data=request.POST,
            instance=None,
            additional_instance_attributes={
                "creator": request.user,
                "language": language,
                "poi": poi_form.instance,
            },
            changed_by_user=request.user,
        )

        if not poi_form.is_valid() or not poi_translation_form.is_valid():
            return JsonResponse(
                data={
                    "success": False,
                },
            )

        poi_translation_form.instance.poi = poi_form.save()
        poi_translation_form.save()

        return JsonResponse(
            data={
                "success": True,
                "poi_address_container": render_to_string(
                    "ajax_poi_form/_poi_address_container.html",
                    {"poi": poi_translation_form.instance.poi},
                ),
                "poi_id": poi_translation_form.instance.poi.id,
            }
        )
