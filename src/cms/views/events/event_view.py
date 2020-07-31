import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...constants import status
from ...decorators import region_permission_required
from ...forms.events import EventForm, EventTranslationForm, RecurrenceRuleForm
from ...models import Region, Language, Event, EventTranslation, RecurrenceRule, POI

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class EventView(PermissionRequiredMixin, TemplateView):
    permission_required = "cms.view_events"
    raise_exception = True

    template_name = "events/event_form.html"

    # pylint: disable=too-many-locals
    def get(self, request, *args, **kwargs):
        language = Language.objects.get(code=kwargs.get("language_code"))

        # get event and event translation objects if they exist, otherwise objects are None
        event_instance = Event.objects.filter(id=kwargs.get("event_id")).first()
        event_translation_instance = EventTranslation.objects.filter(
            event=event_instance, language=language
        ).first()
        recurrence_rule_instance = RecurrenceRule.objects.filter(
            event=event_instance
        ).first()
        poi_instance = POI.objects.filter(events=event_instance).first()

        # Make form disabled if user has no permission to edit the page
        if not request.user.has_perm("cms.edit_events"):
            disabled = True
            messages.warning(
                request, _("You don't have the permission to edit this event.")
            )
        elif event_instance and event_instance.archived:
            disabled = True
            messages.warning(
                request, _("You cannot edit this event because it is archived.")
            )
        else:
            disabled = False

        event_form = EventForm(instance=event_instance, disabled=disabled)
        event_translation_form = EventTranslationForm(
            instance=event_translation_instance, disabled=disabled
        )
        recurrence_rule_form = RecurrenceRuleForm(
            instance=recurrence_rule_instance, disabled=disabled
        )

        return render(
            request,
            self.template_name,
            {
                "current_menu_item": "events",
                "event_form": event_form,
                "event_translation_form": event_translation_form,
                "recurrence_rule_form": recurrence_rule_form,
                "poi": poi_instance,
                "language": language,
                "languages": Region.get_current_region(request).languages
                if event_instance
                else [language],
            },
        )

    # pylint: disable=too-many-locals,too-many-branches
    def post(self, request, **kwargs):
        region = Region.objects.get(slug=kwargs.get("region_slug"))
        language = Language.objects.get(code=kwargs.get("language_code"))
        poi = POI.objects.filter(id=request.POST.get("poi_id")).first()

        event_instance = Event.objects.filter(id=kwargs.get("event_id")).first()
        recurrence_rule_instance = RecurrenceRule.objects.filter(
            event=event_instance
        ).first()
        event_translation_instance = EventTranslation.objects.filter(
            event=event_instance, language=language
        ).first()

        if not request.user.has_perm("cms.edit_events"):
            raise PermissionDenied

        event_form = EventForm(data=request.POST, instance=event_instance,)
        # clean data of event form to be able to pass the cleaned start date to the recurrence form for validation
        event_form_valid = event_form.is_valid()
        recurrence_rule_form = RecurrenceRuleForm(
            data=request.POST,
            instance=recurrence_rule_instance,
            event_start_date=event_form.cleaned_data.get("start_date", None),
        )
        event_translation_form = EventTranslationForm(
            data=request.POST,
            instance=event_translation_instance,
            region=region,
            language=language,
        )

        if (
            not event_form_valid
            or not event_translation_form.is_valid()
            or (
                event_form.cleaned_data["is_recurring"]
                and not recurrence_rule_form.is_valid()
            )
        ):
            forms = [event_form, event_translation_form]
            if event_form.cleaned_data["is_recurring"]:
                forms.append(recurrence_rule_form)
            # Add error messages
            for form in forms:
                for field in form:
                    for error in field.errors:
                        messages.error(request, _(error))
                for error in form.non_field_errors():
                    messages.error(request, _(error))

        elif (
            not event_form.has_changed()
            and not event_translation_form.has_changed()
            and (
                not event_form.cleaned_data["is_recurring"]
                or not recurrence_rule_form.has_changed()
            )
            and poi == event_instance.location
        ):

            messages.info(request, _("No changes detected."))

        else:

            if event_translation_form.instance.status == status.PUBLIC:
                if not request.user.has_perm("cms.publish_events"):
                    raise PermissionDenied

            if event_form.cleaned_data["is_recurring"]:
                recurrence_rule = recurrence_rule_form.save()
            else:
                recurrence_rule = None

            event = event_form.save(
                region=region, recurrence_rule=recurrence_rule, location=poi
            )
            event_translation = event_translation_form.save(
                event=event, user=request.user
            )

            published = event_translation.status == status.PUBLIC
            if not event_instance:
                if published:
                    messages.success(
                        request, _("Event was successfully created and published.")
                    )
                else:
                    messages.success(request, _("Event was successfully created."))
                return redirect(
                    "edit_event",
                    **{
                        "event_id": event.id,
                        "region_slug": region.slug,
                        "language_code": language.code,
                    }
                )
            if not event_translation_instance:
                if published:
                    messages.success(
                        request,
                        _("Event translation was successfully created and published."),
                    )
                else:
                    messages.success(
                        request, _("Event translation was successfully created.")
                    )
            else:
                if published:
                    messages.success(request, _("Event was successfully published."))
                else:
                    messages.success(request, _("Event was successfully saved."))

        return render(
            request,
            self.template_name,
            {
                "current_menu_item": "events",
                "event_form": event_form,
                "event_translation_form": event_translation_form,
                "recurrence_rule_form": recurrence_rule_form,
                "poi": poi,
                "language": language,
                "languages": region.languages if event_instance else [language],
            },
        )
