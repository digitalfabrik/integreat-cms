from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cacheops import invalidate_model
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...constants import status, translation_status
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

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_event"), name="dispatch")
@method_decorator(permission_required("cms.change_event"), name="post")
class EventFormView(
    TemplateView, EventContextMixin, MediaContextMixin, ContentEditLockMixin
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
            kwargs.get("language_slug"), only_active=True
        )

        # get event and event translation objects if they exist, otherwise objects are None
        event_instance = region.events.filter(id=kwargs.get("event_id")).first()
        event_translation_instance = language.event_translations.filter(
            event=event_instance
        ).first()
        recurrence_rule_instance = RecurrenceRule.objects.filter(
            event=event_instance
        ).first()
        # Make form disabled if event is archived or user doesn't have the permission to edit the event
        if event_instance and event_instance.archived:
            disabled = True
            messages.warning(
                request, _("You cannot edit this event because it is archived.")
            )
        elif not request.user.has_perm("cms.change_event"):
            disabled = True
            messages.warning(
                request, _("You don't have the permission to edit events.")
            )
        elif not request.user.has_perm("cms.publish_event"):
            disabled = False
            messages.warning(
                request,
                _(
                    "You don't have the permission to publish events, but you can propose changes and submit them for review instead."
                ),
            )
        else:
            disabled = False

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
            instance=recurrence_rule_instance, disabled=disabled
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
            },
        )

    # pylint: disable=too-many-locals,too-many-branches
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

        event_instance = Event.objects.filter(id=kwargs.get("event_id")).first()
        recurrence_rule_instance = RecurrenceRule.objects.filter(
            event=event_instance
        ).first()
        event_translation_instance = EventTranslation.objects.filter(
            event=event_instance, language=language
        ).first()

        event_form = EventForm(
            data=request.POST,
            files=request.FILES,
            instance=event_instance,
            additional_instance_attributes={"region": region, "location": poi},
        )
        # clean data of event form to be able to pass the cleaned start date to the recurrence form for validation
        event_form_valid = event_form.is_valid()
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
        user_slug = event_translation_form.data.get("slug")

        if (
            not event_form_valid
            or not event_translation_form.is_valid()
            or (
                event_form.cleaned_data["is_recurring"]
                and not recurrence_rule_form.is_valid()
            )
        ):
            # Add error messages
            event_form.add_error_messages(request)
            event_translation_form.add_error_messages(request)
            # do not call recurrence rule form clean method when recurrence rule is not set
            if event_form.cleaned_data["is_recurring"]:
                recurrence_rule_form.add_error_messages(request)
        elif (
            event_translation_form.instance.status == status.AUTO_SAVE
            and not event_form.has_changed()
            and not event_translation_form.has_changed()
            and not recurrence_rule_form.has_changed()
        ):
            messages.info(request, _("No changes detected, autosave skipped"))
        else:
            # Check publish permissions
            if event_translation_form.instance.status in [
                status.DRAFT,
                status.PUBLIC,
            ] and not request.user.has_perm("cms.publish_event"):
                raise PermissionDenied(
                    f"{request.user!r} does not have the permission 'cms.publish_event'"
                )
            # Save forms
            if event_form.cleaned_data.get("is_recurring"):
                # If event is recurring, save recurrence rule
                event_form.instance.recurrence_rule = recurrence_rule_form.save()
            elif event_form.instance.recurrence_rule:
                # If the event is not recurring but it was before, delete the associated recurrence rule
                event_form.instance.recurrence_rule.delete()
                event_form.instance.recurrence_rule = None

            # Save event from event form
            event = event_form.save()
            event_translation_form.instance.event = event
            event_translation_instance = event_translation_form.save(
                foreign_form_changed=(
                    event_form.has_changed() or recurrence_rule_form.has_changed()
                ),
            )

            # Invalidate event translation cache to refresh API result
            invalidate_model(EventTranslation)

            # If any source translation changes to draft, set all depending translations/versions to draft
            if event_translation_form.instance.status == status.DRAFT:
                language_tree_node = region.language_node_by_slug.get(language.slug)
                languages = [language] + [
                    node.language for node in language_tree_node.get_descendants()
                ]
                event_translation_form.instance.event.translations.filter(
                    language__in=languages
                ).update(status=status.DRAFT)

            elif (
                event_translation_form.instance.status == status.PUBLIC
                and event_translation_form.instance.minor_edit
            ):
                event_translation_form.instance.event.translations.filter(
                    language=language
                ).update(status=status.PUBLIC)
            # Show a message that the slug was changed if it was not unique
            if user_slug and user_slug != event_translation_form.cleaned_data["slug"]:
                other_translation = EventTranslation.objects.filter(
                    event__region=region, slug=user_slug, language=language
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

            # Add the success message and redirect to the edit page
            if not event_instance:
                messages.success(
                    request,
                    _('Event "{}" was successfully created').format(
                        event_translation_form.instance
                    ),
                )
            elif (
                not event_form.has_changed()
                and not event_translation_form.has_changed()
                and not recurrence_rule_form.has_changed()
            ):
                messages.info(request, _("No changes detected, but date refreshed"))
            else:
                # Add the success message
                event_translation_form.add_success_message(request)

            return redirect(
                "edit_event",
                **{
                    "event_id": event_form.instance.id,
                    "region_slug": region.slug,
                    "language_slug": language.slug,
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
                "poi": poi,
                "language": language,
                "languages": region.active_languages if event_instance else [language],
                "url_link": url_link,
                "translation_states": (
                    event_instance.translation_states if event_instance else []
                ),
            },
        )
