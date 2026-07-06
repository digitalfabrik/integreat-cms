"""
A view representing an instance of a point of interest. POIs can be created or updated via this view.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cacheops import invalidate_model
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models.signals import post_save
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ....core.signals.contact_signals import contact_save_handler
from ...constants import status, text_directions
from ...decorators import permission_required
from ...forms import ContactForm, POIForm, POITranslationForm
from ...models import Contact, Language, POI, POITranslation
from ...utils.translation_utils import gettext_many_lazy as __
from ...utils.translation_utils import translate_link
from ..media.media_context_mixin import MediaContextMixin
from ..mixins import ContentEditLockMixin
from ..utils.contact_utils import generate_primary_contact_from_poi
from .poi_context_mixin import POIContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

    from integreat_cms.cms.models.regions.region import Region

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_poi"), name="dispatch")
@method_decorator(permission_required("cms.change_poi"), name="post")
class POIFormView(
    TemplateView,
    POIContextMixin,
    MediaContextMixin,
    ContentEditLockMixin,
):
    """
    View for editing POIs
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pois/poi_form.html"
    #: The url name of the view to show if the user decides to go back (see :class:`~integreat_cms.cms.views.mixins.ContentEditLockMixin`)
    back_url_name: str | None = "pois"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render :class:`~integreat_cms.cms.forms.pois.poi_form.POIForm` and :class:`~integreat_cms.cms.forms.pois.poi_translation_form.POITranslationForm`

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        region = request.region
        language = Language.objects.get(slug=kwargs.get("language_slug"))

        # get poi and translation objects if they exist
        poi = POI.objects.filter(id=kwargs.get("poi_id")).first()
        poi_translation = POITranslation.objects.filter(
            poi=poi,
            language=language,
        ).first()
        is_edit = poi is not None

        disabled = self.check_if_poi_is_locked(request, poi)

        poi_form = POIForm(
            instance=poi,
            disabled=disabled,
            additional_instance_attributes={
                "region": region,
            },
        )
        poi_translation_form = POITranslationForm(
            request=request,
            language=language,
            instance=poi_translation,
            disabled=disabled,
            default_language_title=poi.default_translation.title if poi else None,
        )
        url_link = f"{settings.WEBAPP_URL}/{region.slug}/{language.slug}/{poi_translation_form.instance.url_infix}/"

        contact_form = ContactForm(
            additional_instance_attributes={"region": request.region}
        )

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
                "right_to_left": (
                    language.text_direction == text_directions.RIGHT_TO_LEFT
                ),
                "contact_form": contact_form,
                "show_contact_form_widget": False,
                "is_edit": is_edit,
            },
        )

    @transaction.atomic
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Submit :class:`~integreat_cms.cms.forms.pois.poi_form.POIForm` and
        :class:`~integreat_cms.cms.forms.pois.poi_translation_form.POITranslationForm` and save :class:`~integreat_cms.cms.models.pois.poi.POI` and
        :class:`~integreat_cms.cms.models.pois.poi_translation.POITranslation` objects

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        region = request.region
        language = Language.objects.get(slug=kwargs.get("language_slug"))

        poi_id = kwargs.get("poi_id")
        poi_instance, poi_translation_instance = self.get_instances(
            language=language, poi_id=poi_id
        )

        is_edit = poi_instance is not None

        if poi_instance and poi_instance.archived:
            return redirect(
                "edit_poi",
                **{
                    "poi_id": poi_instance.id,
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        poi_form, poi_translation_form = self.instantiate_forms(
            request=request,
            poi_instance=poi_instance,
            poi_translation_instance=poi_translation_instance,
            language=language,
            region=region,
        )

        # Save the user selected slug before is_valid() is called and it is changed for uniqueness
        user_slug = poi_translation_form.data.get("slug")

        phone_number = poi_form.data.get("primary_phone_number")
        email = poi_form.data.get("primary_email")
        website = poi_form.data.get("primary_website")

        data = request.POST.dict()
        new_poi_and_new_related_contact = (
            not is_edit and self.related_contact_data_added(data)
        )

        contact_form = ContactForm(
            request=request,
            data=data,
            instance=None,
            additional_instance_attributes={
                "region": request.region,
            },
        )

        if self.is_qualified_for_save(request, poi_form, poi_translation_form):
            sid = transaction.savepoint()

            if (
                self.validate_and_save_poi(request, poi_form)
                and self.validate_poi_translation(request, poi_translation_form)
                and self.validate_and_save_related_contact(
                    new_poi_and_new_related_contact, poi_form, data, request
                )
            ):
                poi_translation_form.instance.poi = poi_form.instance
                poi_translation_form.save()

                generate_primary_contact_from_poi(
                    website,
                    phone_number,
                    email,
                    poi_form.instance,
                    language,
                    region,
                    poi_translation_form.instance.title,
                )

                # If any source translation changes to draft, set all dependent translations/versions to draft
                self.adjust_status_of_dependent_translations(
                    poi_translation_form,
                    language,
                    region,
                )

                self.show_slug_changed_message(
                    request, language, region, user_slug, poi_translation_form
                )

                # Add the success message and redirect to the edit page
                self.set_success_messages(
                    is_edit=is_edit,
                    request=request,
                    poi_translation_form=poi_translation_form,
                    poi_form=poi_form,
                )

                self.warn_if_coordinates_too_far(request, poi_form)

                self.update_contact_cards(poi_form)

                invalidate_model(Contact)

                return redirect(
                    "edit_poi",
                    **{
                        "poi_id": poi_form.instance.id,
                        "region_slug": region.slug,
                        "language_slug": language.slug,
                    },
                )

            # Failure: rollback and re-instantiate for clean re-render
            transaction.savepoint_rollback(sid)
            poi_instance, poi_translation_instance = self.get_instances(
                language=language, poi_id=poi_id
            )
            poi_form, poi_translation_form = self.instantiate_forms(
                request=request,
                poi_instance=poi_instance,
                poi_translation_instance=poi_translation_instance,
                language=language,
                region=region,
            )

        url_link = f"{settings.WEBAPP_URL}/{region.slug}/{language.slug}/{poi_translation_form.instance.url_infix}/"
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "poi_form": poi_form,
                "poi_translation_form": poi_translation_form,
                "contact_form": contact_form,
                "language": language,
                # Languages for tab view
                "languages": region.active_languages if poi_instance else [language],
                "url_link": url_link,
                "translation_states": (
                    poi_instance.translation_states if poi_instance else []
                ),
                "right_to_left": (
                    language.text_direction == text_directions.RIGHT_TO_LEFT
                ),
                "show_contact_form_widget": new_poi_and_new_related_contact,
                "is_edit": is_edit,
            },
        )

    def update_contact_cards(self, poi_form: POIForm) -> None:
        """
        Send the post save signal of contact model to trigger contact card update
        """
        if "address" in poi_form.changed_data and (
            related_contacts := poi_form.instance.contacts.all()
        ):
            for contact in related_contacts:
                post_save.send(
                    sender=Contact,
                    instance=contact,
                    created=False,
                    using=contact_save_handler,
                )

    def show_slug_changed_message(
        self,
        request: HttpRequest,
        language: Language,
        region: Any,
        user_slug: str,
        poi_translation_form: POITranslationForm,
    ) -> None:
        """
        Shows a message to the user if the slug they provided was not unique and therefore changed.
        """
        if user_slug and user_slug != poi_translation_form.cleaned_data["slug"]:
            other_translation = POITranslation.objects.filter(
                poi__region=region,
                slug=user_slug,
                language=language,
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

    def get_instances(
        self, language: Language, poi_id: Any
    ) -> tuple[POI, POITranslation]:
        poi_instance = POI.objects.filter(id=poi_id).first()
        poi_translation_instance = POITranslation.objects.filter(
            poi=poi_instance,
            language=language,
        ).first()
        return poi_instance, poi_translation_instance

    def instantiate_forms(
        self,
        request: HttpRequest,
        poi_instance: POI,
        poi_translation_instance: POITranslation,
        language: Language,
        region: Any,
    ) -> tuple[POIForm, POITranslationForm]:
        poi_form = POIForm(
            data=request.POST,
            files=request.FILES,
            instance=poi_instance,
            additional_instance_attributes={
                "region": region,
            },
        )
        poi_translation_form = POITranslationForm(
            request=request,
            language=language,
            data=request.POST,
            instance=poi_translation_instance,
            additional_instance_attributes={
                "creator": request.user,
                "language": language,
                "poi": poi_form.instance,
            },
            changed_by_user=request.user,
        )

        return poi_form, poi_translation_form

    def related_contact_data_added(self, data: dict[str, str | list[str]]) -> bool:
        keys_to_check = [
            "area_of_responsibility",
            "name",
            "email",
            "phone_number",
            "mobile_phone_number",
            "website",
        ]
        return any(data.get(k, "") != "" for k in keys_to_check)

    def set_success_messages(
        self,
        is_edit: bool,
        request: HttpRequest,
        poi_translation_form: POITranslationForm,
        poi_form: POIForm,
    ) -> None:
        """
        Show success messages after saving the POI and POITranslation forms.
        """
        if not is_edit:
            messages.success(
                request,
                _('Location "{}" was successfully created').format(
                    poi_translation_form.instance,
                ),
            )
        elif not poi_form.has_changed() and not poi_translation_form.has_changed():
            messages.info(request, _("No changes detected, but date refreshed"))
        else:
            # Add the success message
            poi_translation_form.add_success_message(request)

    def check_if_poi_is_locked(
        self,
        request: HttpRequest,
        poi: POI | None,
    ) -> bool:
        """
        Check if the content is locked for editing.
        """
        disabled = False
        if poi and poi.archived:
            disabled = True
            messages.warning(
                request,
                _("You cannot edit this location because it is archived."),
            )
        elif not request.user.has_perm("cms.change_poi"):
            disabled = True
            messages.warning(
                request,
                _("You don't have the permission to edit locations."),
            )

        return disabled

    def adjust_status_of_dependent_translations(
        self,
        poi_translation_form: POITranslationForm,
        language: Language,
        region: Region,
    ) -> None:
        """
        Change the status of all dependent translations of the POI according to the status of the current translation.
        """
        if poi_translation_form.instance.status == status.DRAFT:
            language_tree_node = region.language_node_by_slug.get(language.slug)
            languages = [language] + [
                node.language for node in language_tree_node.get_descendants()
            ]
            poi_translation_form.instance.poi.translations.filter(
                language__in=languages,
            ).update(status=status.DRAFT)

    def warn_if_coordinates_too_far(
        self, request: HttpRequest, poi_form: POIForm
    ) -> None:
        """
        Warn the user if the manually entered coordinates are too far from the entered address.
        """
        if poi_form.nominatim_distance_delta > 10:
            messages.warning(
                request,
                __(
                    _(
                        "The distance between the manually entered coordinates and the coordinates of the address is {}km.",
                    ).format(poi_form.nominatim_distance_delta),
                    _("Please make sure the entered values are correct."),
                ),
            )

    def is_qualified_for_save(
        self,
        request: HttpRequest,
        poi_form: POIForm,
        poi_translation_form: POITranslationForm,
    ) -> bool:
        """
        Checks whether the current request should proceed with saving the page and translation.
        """
        if (
            poi_translation_form.instance.status == status.AUTO_SAVE
            and not poi_form.has_changed()
            and not poi_translation_form.has_changed()
        ):
            messages.info(request, _("No changes detected, autosave skipped"))
            return False
        return True

    def validate_and_save_poi(self, request: HttpRequest, poi_form: POIForm) -> bool:
        if not poi_form.is_valid():
            poi_form.add_error_messages(request)
            return False
        poi = poi_form.save()
        return poi is not None

    def validate_poi_translation(
        self, request: HttpRequest, poi_translation_form: POITranslationForm
    ) -> bool:
        if not poi_translation_form.is_valid():
            poi_translation_form.add_error_messages(request)
            return False
        return True

    def validate_and_save_related_contact(
        self,
        new_poi_and_new_related_contact: bool,
        poi_form: POIForm,
        data: dict[str, str | list[str]],
        request: HttpRequest,
    ) -> bool:
        # only attempt to create a related contact if we are in creation mode and relevant fields have been added
        if new_poi_and_new_related_contact:
            data.update({"location": poi_form.instance.id, "opening_hours": ""})
            contact_form = ContactForm(
                request=request,
                data=data,
                instance=None,
                additional_instance_attributes={
                    "region": request.region,
                },
            )

            if contact_form.is_valid():
                contact = contact_form.save()
                messages.success(
                    request,
                    _("Contact {} was successfully created").format(
                        contact.get_additional_attribute(),
                    ),
                )
                return True
            contact_form.add_error_messages(request)
            return False
        return True
