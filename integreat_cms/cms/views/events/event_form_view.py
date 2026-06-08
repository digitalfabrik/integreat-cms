from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cacheops import invalidate_model
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...constants import status, text_directions, translation_status
from ...decorators import permission_required
from ...forms import EventForm, EventTranslationForm, RecurrenceRuleForm
from ...models import Event, EventTranslation, Language, POI, RecurrenceRule
from ...utils.translation_utils import translate_link
from ..media.media_context_mixin import MediaContextMixin
from ..mixins import ContentEditLockMixin
from .event_context_mixin import EventContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

    from integreat_cms.cms.models.regions.region import Region

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_event"), name="dispatch")
@method_decorator(permission_required("cms.change_event"), name="post")
class EventFormView(
    TemplateView,
    EventContextMixin,
    MediaContextMixin,
    ContentEditLockMixin,
):
    """
    Class for rendering the events form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "events/event_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"translation_status": translation_status}
    #: The url name of the view to show if the user decides to go back (see :class:`~integreat_cms.cms.views.mixins.ContentEditLockMixin`
    back_url_name: str | None = "events"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render event form for HTTP GET requests

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        region = request.region
        language = region.get_language_or_404(
            kwargs.get("language_slug"),
            only_active=True,
        )

        event_instance = region.events.filter(id=kwargs.get("event_id")).first()
        event_translation_instance = language.event_translations.filter(
            event=event_instance,
        ).first()
        recurrence_rule_instance = RecurrenceRule.objects.filter(
            event=event_instance,
        ).first()

        disabled = self.check_if_event_is_locked(request, event_instance)
        event_form = EventForm(
            instance=event_instance,
            disabled=disabled,
        )
        event_translation_form = EventTranslationForm(
            request=request,
            language=language,
            instance=event_translation_instance,
            disabled=disabled,
        )
        recurrence_rule_form = RecurrenceRuleForm(
            instance=recurrence_rule_instance,
            disabled=disabled,
            initial={
                "recurrence_end_date": (
                    recurrence_rule_instance.recurrence_end_date
                    if recurrence_rule_instance
                    else None
                )
            },
        )

        url_link = f"{settings.WEBAPP_URL}/{region.slug}/{language.slug}/{event_translation_form.instance.url_infix}/"
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "event_form": event_form,
                "event_translation_form": event_translation_form,
                "recurrence_rule_form": recurrence_rule_form,
                "poi": event_instance.location if event_instance else None,
                "language": language,
                "languages": region.active_languages if event_instance else [language],
                "url_link": url_link,
                "translation_states": (
                    event_instance.translation_states if event_instance else []
                ),
                "disabled": disabled,
                "right_to_left": (
                    language.text_direction == text_directions.RIGHT_TO_LEFT
                ),
            },
        )

    @transaction.atomic
    def post(self, request: HttpRequest, **kwargs: Any) -> HttpResponse:
        r"""
        Save event and ender event form for HTTP POST requests

        :param request: Object representing the user call
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to publish events

        :return: The rendered template response
        """
        region = request.region
        language = Language.objects.get(slug=kwargs.get("language_slug"))
        poi = POI.objects.filter(id=request.POST.get("location")).first()

        event_id = kwargs.get("event_id")
        event_instance, event_translation_instance, recurrence_rule_instance = (
            self.get_instances(language=language, event_id=event_id)
        )

        event_form, event_translation_form, recurrence_rule_form = (
            self.instantiate_forms(
                request=request,
                event_instance=event_instance,
                recurrence_rule_instance=recurrence_rule_instance,
                event_translation_instance=event_translation_instance,
                poi=poi,
                language=language,
                region=region,
            )
        )

        # Save the user selected slug before is_valid() is called and it is changed for uniqueness
        user_slug = event_translation_form.data.get("slug")

        if self.is_qualified_for_save(
            request, event_form, event_translation_form, recurrence_rule_form
        ):
            sid = transaction.savepoint()

            if (
                self.validate_and_save_event(request, event_form)
                and self.validate_event_translation(request, event_translation_form)
                and self.validate_recurrence_rule(
                    request, event_form, recurrence_rule_form
                )
            ):
                event_translation_instance = event_translation_form.save(
                    foreign_form_changed=(
                        event_form.has_changed() or recurrence_rule_form.has_changed()
                    ),
                )

                self.update_recurrence_rule(event_form, recurrence_rule_form)

                # If any source translation changes to draft, set all dependent translations/versions to draft
                self.adjust_status_of_dependent_translations(
                    event_translation_form,
                    language,
                    region,
                )

                self.show_slug_changed_message(
                    request, language, region, user_slug, event_translation_form
                )

                forms_unchanged = (
                    not event_form.has_changed()
                    and not event_translation_form.has_changed()
                    and not recurrence_rule_form.has_changed()
                )
                self.add_success_message(
                    request, event_instance, forms_unchanged, event_translation_form
                )

                # Invalidate event translation cache to refresh API result
                invalidate_model(EventTranslation)

                return redirect(
                    "edit_event",
                    **{
                        "event_id": event_form.instance.id,
                        "region_slug": region.slug,
                        "language_slug": language.slug,
                    },
                )

            # Failure: rollback and re-instantiate for clean re-render
            transaction.savepoint_rollback(sid)
            event_instance, event_translation_instance, recurrence_rule_instance = (
                self.get_instances(language=language, event_id=event_id)
            )
            event_form, event_translation_form, recurrence_rule_form = (
                self.instantiate_forms(
                    request=request,
                    event_instance=event_instance,
                    recurrence_rule_instance=recurrence_rule_instance,
                    event_translation_instance=event_translation_instance,
                    poi=poi,
                    language=language,
                    region=region,
                )
            )
        url_link = f"{settings.WEBAPP_URL}/{region.slug}/{language.slug}/{event_translation_form.instance.url_infix}/"
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "event_form": event_form,
                "event_translation_form": event_translation_form,
                "recurrence_rule_form": recurrence_rule_form,
                "poi": poi,
                "language": language,
                "languages": region.active_languages if event_instance else [language],
                "url_link": url_link,
                "translation_states": (
                    event_instance.translation_states if event_instance else []
                ),
                "right_to_left": (
                    language.text_direction == text_directions.RIGHT_TO_LEFT
                ),
            },
        )

    def instantiate_forms(
        self,
        request: HttpRequest,
        event_instance: Event,
        recurrence_rule_instance: RecurrenceRule,
        event_translation_instance: EventTranslation,
        poi: POI,
        region: Region,
        language: Language,
    ) -> tuple[EventForm, EventTranslationForm, RecurrenceRuleForm]:
        event_form = EventForm(
            data=request.POST,
            files=request.FILES,
            instance=event_instance,
            additional_instance_attributes={"region": region, "location": poi},
        )

        event_form.is_valid()  # populate cleaned_data

        recurrence_rule_form = RecurrenceRuleForm(
            data=request.POST,
            instance=recurrence_rule_instance,
            event_start_date=event_form.cleaned_data.get("start_date", None),
        )
        event_translation_form = EventTranslationForm(
            request=request,
            language=language,
            data=request.POST,
            instance=event_translation_instance,
            additional_instance_attributes={
                "creator": request.user,
                "language": language,
                "event": event_form.instance,
            },
            changed_by_user=request.user,
        )
        return event_form, event_translation_form, recurrence_rule_form

    def get_instances(
        self, language: Language, event_id: Any
    ) -> tuple[Event, EventTranslation, RecurrenceRule]:
        event_instance = Event.objects.filter(id=event_id).first()
        recurrence_rule_instance = RecurrenceRule.objects.filter(
            event=event_instance,
        ).first()
        event_translation_instance = EventTranslation.objects.filter(
            event=event_instance,
            language=language,
        ).first()
        return event_instance, event_translation_instance, recurrence_rule_instance

    def check_if_event_is_locked(
        self,
        request: HttpRequest,
        event_instance: Event | None,
    ) -> bool:
        """
        Checks if the event is locked for editing and should be disabled, or not
        """
        disabled = False
        if event_instance and event_instance.archived:
            disabled = True
            messages.warning(
                request,
                _("You cannot edit this event because it is archived."),
            )
        elif event_instance and event_instance.external_calendar:
            disabled = True
            messages.warning(
                request,
                _(
                    "You cannot edit this event because it was imported from an external calendar.",
                ),
            )
        elif not request.user.has_perm("cms.change_event"):
            disabled = True
            messages.warning(
                request,
                _("You don't have the permission to edit events."),
            )
        elif not request.user.has_perm("cms.publish_event"):
            disabled = False
            messages.warning(
                request,
                _(
                    "You don't have the permission to publish events, but you can propose changes and submit them for review instead.",
                ),
            )

        return disabled

    def show_slug_changed_message(
        self,
        request: HttpRequest,
        language: Language,
        region: Region,
        user_slug: str,
        event_translation_form: EventTranslationForm,
    ) -> None:
        """
        Shows a message to the user if the slug they provided was not unique and therefore changed.
        """
        if user_slug and user_slug != event_translation_form.cleaned_data["slug"]:
            other_translation = EventTranslation.objects.filter(
                event__region=region,
                slug=user_slug,
                language=language,
            ).first()
            other_translation_link = other_translation.backend_edit_link
            message = _(
                "The slug was changed from '{user_slug}' to '{slug}', "
                "because '{user_slug}' is already used by <a>{translation}</a> or one of its previous versions.",
            ).format(
                user_slug=user_slug,
                slug=event_translation_form.cleaned_data["slug"],
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

    def add_success_message(
        self,
        request: HttpRequest,
        event_instance: Event | None,
        forms_unchanged: bool = False,
        event_translation_form: EventTranslationForm | None = None,
    ) -> None:
        """
        Adds success messages to the request.
        """
        if event_translation_form and not event_instance:
            messages.success(
                request,
                _('Event "{}" was successfully created').format(
                    event_translation_form.instance,
                ),
            )
        elif forms_unchanged:
            messages.info(request, _("No changes detected, but date refreshed"))
        elif event_translation_form:
            event_translation_form.add_success_message(request)

    def adjust_status_of_dependent_translations(
        self,
        event_translation_form: EventTranslationForm,
        language: Language,
        region: Region,
    ) -> None:
        """
        Adjusts the translation statuses of all dependent translations of the event.
        """
        if event_translation_form.instance.status == status.DRAFT:
            language_tree_node = region.language_node_by_slug.get(language.slug)
            languages = [language] + [
                node.language for node in language_tree_node.get_descendants()
            ]
            event_translation_form.instance.event.translations.filter(
                language__in=languages,
            ).update(status=status.DRAFT)

        elif (
            event_translation_form.instance.status == status.PUBLIC
            and event_translation_form.instance.minor_edit
        ):
            event_translation_form.instance.event.translations.filter(
                language=language,
            ).update(status=status.PUBLIC)

    def is_qualified_for_save(
        self,
        request: HttpRequest,
        event_form: EventForm,
        event_translation_form: EventTranslationForm,
        recurrence_rule_form: RecurrenceRuleForm,
    ) -> bool:
        """
        Checks whether the current request should proceed with saving the event and translation.
        """
        if request.POST.get("status") in [
            status.DRAFT,
            status.PUBLIC,
        ] and not request.user.has_perm("cms.publish_event"):
            raise PermissionDenied(
                f"{request.user!r} does not have the permission 'cms.publish_event'",
            )

        if (
            event_translation_form.instance.status == status.AUTO_SAVE
            and not event_form.has_changed()
            and not event_translation_form.has_changed()
            and not recurrence_rule_form.has_changed()
        ):
            messages.info(request, _("No changes detected, autosave skipped"))
            return False
        return True

    def validate_and_save_event(
        self, request: HttpRequest, event_form: EventForm
    ) -> bool:
        if not event_form.is_valid():
            event_form.add_error_messages(request)
            return False
        event = event_form.save()
        return event is not None

    def validate_event_translation(
        self, request: HttpRequest, event_translation_form: EventTranslationForm
    ) -> bool:
        if not event_translation_form.is_valid():
            event_translation_form.add_error_messages(request)
            return False
        return True

    def validate_recurrence_rule(
        self,
        request: HttpRequest,
        event_form: EventForm,
        recurrence_rule_form: RecurrenceRuleForm,
    ) -> bool:
        if (
            event_form.cleaned_data.get("is_recurring")
            and not recurrence_rule_form.is_valid()
        ):
            recurrence_rule_form.add_error_messages(request)
            return False
        return True

    def update_recurrence_rule(
        self, event_form: EventForm, recurrence_rule_form: RecurrenceRuleForm
    ) -> None:
        if event_form.cleaned_data.get("is_recurring"):
            # If event is recurring, save recurrence rule
            event_form.instance.recurrence_rule = recurrence_rule_form.save()
            event_form.instance.save(update_fields=["recurrence_rule"])
        elif event_form.instance.recurrence_rule:
            # If the event is not recurring but it was before, delete the associated recurrence rule
            event_form.instance.recurrence_rule.delete()
            event_form.instance.recurrence_rule = None
            event_form.instance.save(update_fields=["recurrence_rule"])
