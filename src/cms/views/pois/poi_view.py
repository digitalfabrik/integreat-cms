"""
A view representing an instance of a point of interest. POIs can be created or updated via this view.
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...constants import status
from ...decorators import region_permission_required
from ...forms import POIForm, POITranslationForm
from ...models import POI, POITranslation, Region, Language
from .poi_context_mixin import POIContextMixin

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
# pylint: disable=too-many-ancestors
class POIView(PermissionRequiredMixin, TemplateView, POIContextMixin):
    """
    View for editing POIs
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_pois"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pois/poi_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "pois_form"}

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.pois.poi_form.POIForm` and :class:`~cms.forms.pois.poi_translation_form.POITranslationForm`

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
        language = Language.objects.get(slug=kwargs.get("language_slug"))

        # get poi and translation objects if they exist
        poi = POI.objects.filter(id=kwargs.get("poi_id")).first()
        poi_translation = POITranslation.objects.filter(
            poi=poi,
            language=language,
        ).first()

        if poi and poi.archived:
            messages.warning(
                request, _("You cannot edit this location because it is archived.")
            )

        poi_form = POIForm(instance=poi)
        poi_translation_form = POITranslationForm(instance=poi_translation)
        context = self.get_context_data(**kwargs)
        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                **context,
                "poi_form": poi_form,
                "poi_translation_form": poi_translation_form,
                "language": language,
                # Languages for tab view
                "languages": region.languages if poi else [language],
            },
        )

    # pylint: disable=too-many-branches,too-many-locals,unused-argument
    def post(self, request, *args, **kwargs):
        """
        Submit :class:`~cms.forms.pois.poi_form.POIForm` and
        :class:`~cms.forms.pois.poi_translation_form.POITranslationForm` and save :class:`~cms.models.pois.poi.POI` and
        :class:`~cms.models.pois.poi_translation.POITranslation` objects

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
        language = Language.objects.get(slug=kwargs.get("language_slug"))

        poi_instance = POI.objects.filter(id=kwargs.get("poi_id")).first()
        poi_translation_instance = POITranslation.objects.filter(
            poi=poi_instance,
            language=language,
        ).first()

        if poi_instance and poi_instance.archived:
            return redirect(
                "edit_poi",
                **{
                    "poi_id": poi_instance.id,
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                }
            )

        poi_form = POIForm(
            data=request.POST,
            files=request.FILES,
            instance=poi_instance,
        )
        poi_translation_form = POITranslationForm(
            request.POST,
            instance=poi_translation_instance,
            region=region,
            language=language,
        )

        if not poi_form.is_valid() or not poi_translation_form.is_valid():

            # Add error messages
            for form in [poi_form, poi_translation_form]:
                for field in form:
                    for error in field.errors:
                        messages.error(request, _(field.label) + ": " + _(error))
                for error in form.non_field_errors():
                    messages.error(request, _(error))

            return render(
                request,
                self.template_name,
                {
                    **self.base_context,
                    **self.get_context_data(**kwargs),
                    "poi_form": poi_form,
                    "poi_translation_form": poi_translation_form,
                    "language": language,
                    # Languages for tab view
                    "languages": region.languages if poi_instance else [language],
                },
            )

        if not poi_form.has_changed() and not poi_translation_form.has_changed():

            messages.info(request, _("No changes detected"))

            return render(
                request,
                self.template_name,
                {
                    **self.base_context,
                    **self.get_context_data(**kwargs),
                    "poi_form": poi_form,
                    "poi_translation_form": poi_translation_form,
                    "language": language,
                    # Languages for tab view
                    "languages": region.languages if poi_instance else [language],
                },
            )

        poi = poi_form.save(region=region)
        poi_translation_form.save(poi=poi, user=request.user)

        published = poi_translation_form.instance.status == status.PUBLIC
        if not poi_instance:
            if published:
                messages.success(
                    request, _("Location was successfully created and published")
                )
            else:
                messages.success(request, _("Location was successfully created"))
        else:
            if published:
                messages.success(request, _("Location was successfully published"))
            else:
                messages.success(request, _("Location was successfully saved"))
        return redirect(
            "edit_poi",
            **{
                "poi_id": poi.id,
                "region_slug": region.slug,
                "language_slug": language.slug,
            }
        )
