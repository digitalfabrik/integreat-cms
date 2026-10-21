"""
A view representing an instance of a place. Places can be created or updated via this view.
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
from ...forms import ContactForm, PlaceForm, PlaceTranslationForm
from ...models import Contact, Language, Place, PlaceTranslation
from ...utils.translation_utils import gettext_many_lazy as __
from ...utils.translation_utils import translate_link
from ..media.media_context_mixin import MediaContextMixin
from ..mixins import ContentEditLockMixin
from ..utils.contact_utils import generate_primary_contact_from_place
from .place_context_mixin import PlaceContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

    from integreat_cms.cms.models.regions.region import Region

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_place"), name="dispatch")
@method_decorator(permission_required("cms.change_place"), name="post")
class PlaceFormView(
    TemplateView,
    PlaceContextMixin,
    MediaContextMixin,
    ContentEditLockMixin,
):
    """
    View for editing places
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "places/place_form.html"
    #: The url name of the view to show if the user decides to go back (see :class:`~integreat_cms.cms.views.mixins.ContentEditLockMixin`)
    back_url_name: str | None = "places"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render :class:`~integreat_cms.cms.forms.places.place_form.PlaceForm` and :class:`~integreat_cms.cms.forms.places.place_translation_form.PlaceTranslationForm`

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        region = request.region
        language = Language.objects.get(slug=kwargs.get("language_slug"))

        # get place and translation objects if they exist
        place = Place.objects.filter(id=kwargs.get("place_id")).first()
        place_translation = PlaceTranslation.objects.filter(
            place=place,
            language=language,
        ).first()
        is_edit = place is not None

        disabled = self.check_if_place_is_locked(request, place)

        place_form = PlaceForm(
            instance=place,
            disabled=disabled,
            additional_instance_attributes={
                "region": region,
            },
        )
        place_translation_form = PlaceTranslationForm(
            request=request,
            language=language,
            instance=place_translation,
            disabled=disabled,
            default_language_title=place.default_translation.title if place else None,
        )
        url_link = f"{settings.WEBAPP_URL}/{region.slug}/{language.slug}/{place_translation_form.instance.url_infix}/"

        contact_form = ContactForm(
            additional_instance_attributes={"region": request.region}
        )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "place_form": place_form,
                "place_translation_form": place_translation_form,
                "language": language,
                # Languages for tab view
                "languages": region.active_languages if place else [language],
                "url_link": url_link,
                "translation_states": place.translation_states if place else [],
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
        Submit :class:`~integreat_cms.cms.forms.places.place_form.PlaceForm` and
        :class:`~integreat_cms.cms.forms.places.place_translation_form.PlaceTranslationForm` and save :class:`~integreat_cms.cms.models.places.place.Place` and
        :class:`~integreat_cms.cms.models.places.place_translation.PlaceTranslation` objects

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        region = request.region
        language = Language.objects.get(slug=kwargs.get("language_slug"))

        place_id = kwargs.get("place_id")
        place_instance, place_translation_instance = self.get_instances(
            language=language, place_id=place_id
        )

        is_edit = place_instance is not None

        if place_instance and place_instance.archived:
            return redirect(
                "edit_place",
                **{
                    "place_id": place_instance.id,
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        place_form, place_translation_form = self.instantiate_forms(
            request=request,
            place_instance=place_instance,
            place_translation_instance=place_translation_instance,
            language=language,
            region=region,
        )

        # Save the user selected slug before is_valid() is called and it is changed for uniqueness
        user_slug = place_translation_form.data.get("slug")

        phone_number = place_form.data.get("primary_phone_number")
        email = place_form.data.get("primary_email")
        website = place_form.data.get("primary_website")

        data = request.POST.dict()
        new_place_and_new_related_contact = (
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

        if self.is_qualified_for_save(request, place_form, place_translation_form):
            sid = transaction.savepoint()

            if (
                self.validate_and_save_place(request, place_form)
                and self.validate_place_translation(request, place_translation_form)
                and self.validate_and_save_related_contact(
                    new_place_and_new_related_contact, place_form, data, request
                )
            ):
                place_translation_form.instance.place = place_form.instance
                place_translation_form.save()

                generate_primary_contact_from_place(
                    website,
                    phone_number,
                    email,
                    place_form.instance,
                    language,
                    region,
                    place_translation_form.instance.title,
                )

                # If any source translation changes to draft, set all dependent translations/versions to draft
                self.adjust_status_of_dependent_translations(
                    place_translation_form,
                    language,
                    region,
                )

                self.show_slug_changed_message(
                    request, language, region, user_slug, place_translation_form
                )

                # Add the success message and redirect to the edit page
                self.set_success_messages(
                    is_edit=is_edit,
                    request=request,
                    place_translation_form=place_translation_form,
                    place_form=place_form,
                )

                self.warn_if_coordinates_too_far(request, place_form)

                self.update_contact_cards(place_form)

                invalidate_model(Contact)

                return redirect(
                    "edit_place",
                    **{
                        "place_id": place_form.instance.id,
                        "region_slug": region.slug,
                        "language_slug": language.slug,
                    },
                )

            # Failure: rollback and re-instantiate for clean re-render
            transaction.savepoint_rollback(sid)
            place_instance, place_translation_instance = self.get_instances(
                language=language, place_id=place_id
            )
            place_form, place_translation_form = self.instantiate_forms(
                request=request,
                place_instance=place_instance,
                place_translation_instance=place_translation_instance,
                language=language,
                region=region,
            )

        url_link = f"{settings.WEBAPP_URL}/{region.slug}/{language.slug}/{place_translation_form.instance.url_infix}/"
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "place_form": place_form,
                "place_translation_form": place_translation_form,
                "contact_form": contact_form,
                "language": language,
                # Languages for tab view
                "languages": region.active_languages if place_instance else [language],
                "url_link": url_link,
                "translation_states": (
                    place_instance.translation_states if place_instance else []
                ),
                "right_to_left": (
                    language.text_direction == text_directions.RIGHT_TO_LEFT
                ),
                "show_contact_form_widget": new_place_and_new_related_contact,
                "is_edit": is_edit,
            },
        )

    def update_contact_cards(self, place_form: PlaceForm) -> None:
        """
        Send the post save signal of contact model to trigger contact card update
        """
        if "address" in place_form.changed_data and (
            related_contacts := place_form.instance.contacts.all()
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
        place_translation_form: PlaceTranslationForm,
    ) -> None:
        """
        Shows a message to the user if the slug they provided was not unique and therefore changed.
        """
        cleaned_slug = place_translation_form.cleaned_data["slug"]
        if user_slug and user_slug != cleaned_slug:
            if user_slug.lower() == cleaned_slug:
                message_uppercase = _(
                    "The slug was changed from '{user_slug}' to '{slug}', because uppercase letters are not allowed."
                ).format(
                    user_slug=user_slug,
                    slug=cleaned_slug,
                )
                messages.warning(request, message_uppercase)
            else:
                other_translation = PlaceTranslation.objects.filter(
                    place__region=region,
                    slug=user_slug,
                    language=language,
                ).first()
                if other_translation:
                    other_translation_link = other_translation.backend_edit_link
                    message = _(
                        "The slug was changed from '{user_slug}' to '{slug}', "
                        "because '{user_slug}' is already used by <a>{translation}</a> or one of its previous versions.",
                    ).format(
                        user_slug=user_slug,
                        slug=cleaned_slug,
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
                else:
                    logger.warning(
                        "Slug was changed from the one the user provided, but we can't find the translation that already used it: %s (cleaned to %s)",
                        user_slug,
                        place_translation_form.cleaned_data["slug"],
                    )
                    messages.warning(
                        request,
                        _(
                            "The slug was changed from '{user_slug}' to '{slug}'."
                        ).format(
                            user_slug=user_slug,
                            slug=place_translation_form.cleaned_data["slug"],
                        ),
                    )

    def get_instances(
        self, language: Language, place_id: Any
    ) -> tuple[Place, PlaceTranslation]:
        place_instance = Place.objects.filter(id=place_id).first()
        place_translation_instance = PlaceTranslation.objects.filter(
            place=place_instance,
            language=language,
        ).first()
        return place_instance, place_translation_instance

    def instantiate_forms(
        self,
        request: HttpRequest,
        place_instance: Place,
        place_translation_instance: PlaceTranslation,
        language: Language,
        region: Any,
    ) -> tuple[PlaceForm, PlaceTranslationForm]:
        place_form = PlaceForm(
            data=request.POST,
            files=request.FILES,
            instance=place_instance,
            additional_instance_attributes={
                "region": region,
            },
        )
        place_translation_form = PlaceTranslationForm(
            request=request,
            language=language,
            data=request.POST,
            instance=place_translation_instance,
            additional_instance_attributes={
                "creator": request.user,
                "language": language,
                "place": place_form.instance,
            },
            changed_by_user=request.user,
        )

        return place_form, place_translation_form

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
        place_translation_form: PlaceTranslationForm,
        place_form: PlaceForm,
    ) -> None:
        """
        Show success messages after saving the place and PlaceTranslation forms.
        """
        if not is_edit:
            messages.success(
                request,
                _('Place "{}" was successfully created').format(
                    place_translation_form.instance,
                ),
            )
        elif not place_form.has_changed() and not place_translation_form.has_changed():
            messages.info(request, _("No changes detected, but date refreshed"))
        else:
            # Add the success message
            place_translation_form.add_success_message(request)

    def check_if_place_is_locked(
        self,
        request: HttpRequest,
        place: Place | None,
    ) -> bool:
        """
        Check if the content is locked for editing.
        """
        disabled = False
        if place and place.archived:
            disabled = True
            messages.warning(
                request,
                _("You cannot edit this place because it is archived."),
            )
        elif not request.user.has_perm("cms.change_place"):
            disabled = True
            messages.warning(
                request,
                _("You don't have the permission to edit places."),
            )

        return disabled

    def adjust_status_of_dependent_translations(
        self,
        place_translation_form: PlaceTranslationForm,
        language: Language,
        region: Region,
    ) -> None:
        """
        Change the status of all dependent translations of the place according to the status of the current translation.
        """
        if place_translation_form.instance.status == status.DRAFT:
            language_tree_node = region.language_node_by_slug.get(language.slug)
            languages = [language] + [
                node.language for node in language_tree_node.get_descendants()
            ]
            place_translation_form.instance.place.translations.filter(
                language__in=languages,
            ).update(status=status.DRAFT)

    def warn_if_coordinates_too_far(
        self, request: HttpRequest, place_form: PlaceForm
    ) -> None:
        """
        Warn the user if the manually entered coordinates are too far from the entered address.
        """
        if place_form.nominatim_distance_delta > 10:
            messages.warning(
                request,
                __(
                    _(
                        "The distance between the manually entered coordinates and the coordinates of the address is {}km.",
                    ).format(place_form.nominatim_distance_delta),
                    _("Please make sure the entered values are correct."),
                ),
            )

    def is_qualified_for_save(
        self,
        request: HttpRequest,
        place_form: PlaceForm,
        place_translation_form: PlaceTranslationForm,
    ) -> bool:
        """
        Checks whether the current request should proceed with saving the page and translation.
        """
        if (
            place_translation_form.instance.status == status.AUTO_SAVE
            and not place_form.has_changed()
            and not place_translation_form.has_changed()
        ):
            messages.info(request, _("No changes detected, autosave skipped"))
            return False
        return True

    def validate_and_save_place(
        self, request: HttpRequest, place_form: PlaceForm
    ) -> bool:
        if not place_form.is_valid():
            place_form.add_error_messages(request)
            return False
        place = place_form.save()
        return place is not None

    def validate_place_translation(
        self, request: HttpRequest, place_translation_form: PlaceTranslationForm
    ) -> bool:
        if not place_translation_form.is_valid():
            place_translation_form.add_error_messages(request)
            return False
        return True

    def validate_and_save_related_contact(
        self,
        new_place_and_new_related_contact: bool,
        place_form: PlaceForm,
        data: dict[str, str | list[str]],
        request: HttpRequest,
    ) -> bool:
        # only attempt to create a related contact if we are in creation mode and relevant fields have been added
        if new_place_and_new_related_contact:
            data.update({"place": place_form.instance.id, "opening_hours": ""})
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
