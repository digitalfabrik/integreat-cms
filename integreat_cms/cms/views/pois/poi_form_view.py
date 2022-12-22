"""
A view representing an instance of a point of interest. POIs can be created or updated via this view.
"""
import logging

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from ...constants import status
from ...decorators import permission_required
from ...forms import POIForm, POITranslationForm
from ...models import POI, POITranslation, Language
from ...utils.translation_utils import translate_link, gettext_many_lazy as __
from ..media.media_context_mixin import MediaContextMixin
from ..mixins import ContentEditLockMixin
from .poi_context_mixin import POIContextMixin

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_poi"), name="dispatch")
@method_decorator(permission_required("cms.change_poi"), name="post")
class POIFormView(
    TemplateView, POIContextMixin, MediaContextMixin, ContentEditLockMixin
):
    """
    View for editing POIs
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pois/poi_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "pois_form"}
    #: The url name of the view to show if the user decides to go back (see :class:`~integreat_cms.cms.views.mixins.ContentEditLockMixin`)
    back_url_name = "pois"

    def get(self, request, *args, **kwargs):
        r"""
        Render :class:`~integreat_cms.cms.forms.pois.poi_form.POIForm` and :class:`~integreat_cms.cms.forms.pois.poi_translation_form.POITranslationForm`

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = request.region
        language = Language.objects.get(slug=kwargs.get("language_slug"))

        # get poi and translation objects if they exist
        poi = POI.objects.filter(id=kwargs.get("poi_id")).first()
        poi_translation = POITranslation.objects.filter(
            poi=poi,
            language=language,
        ).first()

        if poi and poi.archived:
            disabled = True
            messages.warning(
                request, _("You cannot edit this location because it is archived.")
            )
        elif not request.user.has_perm("cms.change_poi"):
            disabled = True
            messages.warning(
                request, _("You don't have the permission to edit locations.")
            )
        else:
            disabled = False

        poi_form = POIForm(instance=poi, disabled=disabled)
        poi_translation_form = POITranslationForm(
            instance=poi_translation,
            disabled=disabled,
            default_language_title=poi.default_translation.title if poi else None,
        )
        url_link = f"{settings.WEBAPP_URL}/{region.slug}/{language.slug}/{poi_translation_form.instance.url_infix}/"
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "poi_form": poi_form,
                "poi_translation_form": poi_translation_form,
                "language": language,
                # Languages for tab view
                "languages": region.active_languages if poi else [language],
                "url_link": url_link,
                "translation_states": poi.translation_states if poi else [],
            },
        )

    # pylint: disable=too-many-branches,too-many-locals,unused-argument
    def post(self, request, *args, **kwargs):
        r"""
        Submit :class:`~integreat_cms.cms.forms.pois.poi_form.POIForm` and
        :class:`~integreat_cms.cms.forms.pois.poi_translation_form.POITranslationForm` and save :class:`~integreat_cms.cms.models.pois.poi.POI` and
        :class:`~integreat_cms.cms.models.pois.poi_translation.POITranslation` objects

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = request.region
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
                },
            )

        poi_form = POIForm(
            data=request.POST,
            files=request.FILES,
            instance=poi_instance,
            additional_instance_attributes={
                "region": region,
            },
        )
        poi_translation_form = POITranslationForm(
            data=request.POST,
            instance=poi_translation_instance,
            additional_instance_attributes={
                "creator": request.user,
                "language": language,
                "poi": poi_form.instance,
            },
            changed_by_user=request.user,
        )
        user_slug = poi_translation_form.data.get("slug")

        if not poi_form.is_valid() or not poi_translation_form.is_valid():
            # Add error messages
            poi_form.add_error_messages(request)
            poi_translation_form.add_error_messages(request)
        elif (
            poi_translation_form.instance.status == status.AUTO_SAVE
            and not poi_form.has_changed()
            and not poi_translation_form.has_changed()
        ):
            messages.info(request, _("No changes detected, autosave skipped"))
        else:
            # Save forms
            poi_translation_form.instance.poi = poi_form.save()
            poi_translation_form.save(foreign_form_changed=poi_form.has_changed())
            # If any source translation changes to draft, set all depending translations/versions to draft
            if poi_translation_form.instance.status == status.DRAFT:
                language_tree_node = region.language_node_by_slug.get(language.slug)
                languages = [language] + [
                    node.language for node in language_tree_node.get_descendants()
                ]
                poi_translation_form.instance.poi.translations.filter(
                    language__in=languages
                ).update(status=status.DRAFT)
            elif (
                poi_translation_form.instance.status == status.PUBLIC
                and poi_translation_form.instance.minor_edit
            ):
                poi_translation_form.instance.poi.translations.filter(
                    language=language
                ).update(status=status.PUBLIC)

            # Show a message that the slug was changed if it was not unique
            if user_slug and user_slug != poi_translation_form.cleaned_data["slug"]:
                other_translation = POITranslation.objects.filter(
                    poi__region=region, slug=user_slug, language=language
                ).first()
                other_translation_link = other_translation.backend_edit_link
                message = _(
                    "The slug was changed from '{user_slug}' to '{slug}', "
                    "because '{user_slug}' is already used by <a>{translation}</a> or one of its previous versions.",
                ).format(
                    user_slug=user_slug,
                    slug=poi_translation_form.cleaned_data["slug"],
                    translation=other_translation,
                )
                messages.warning(
                    request,
                    translate_link(
                        message,
                        attributes={
                            "href": other_translation_link,
                            "class": "underline hover:no-underline",
                        },
                    ),
                )

            # Add the success message and redirect to the edit page
            if not poi_instance:
                messages.success(
                    request,
                    _('Location "{}" was successfully created').format(
                        poi_translation_form.instance
                    ),
                )
            elif not poi_form.has_changed() and not poi_translation_form.has_changed():
                messages.info(request, _("No changes detected, but date refreshed"))
            else:
                # Add the success message
                poi_translation_form.add_success_message(request)
            # Show warning if nominatim result is more than 10km away from manually entered coordinates
            if poi_form.nominatim_distance_delta > 10:
                messages.warning(
                    request,
                    __(
                        _(
                            "The distance between the manually entered coordinates and the coordinates of the address is {}km."
                        ).format(poi_form.nominatim_distance_delta),
                        _("Please make sure the entered values are correct."),
                    ),
                )
            return redirect(
                "edit_poi",
                **{
                    "poi_id": poi_form.instance.id,
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )
        url_link = f"{settings.WEBAPP_URL}/{region.slug}/{language.slug}/{poi_translation_form.instance.url_infix}/"
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "poi_form": poi_form,
                "poi_translation_form": poi_translation_form,
                "language": language,
                # Languages for tab view
                "languages": region.active_languages if poi_instance else [language],
                "url_link": url_link,
                "translation_states": poi_instance.translation_states
                if poi_instance
                else [],
            },
        )
