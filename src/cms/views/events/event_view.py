import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...constants import status
from ...decorators import region_permission_required
from ...forms import EventForm, EventTranslationForm, RecurrenceRuleForm
from ...models import Region, Language, Event, EventTranslation, RecurrenceRule, POI
from .event_context_mixin import EventContextMixin

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
# pylint: disable=too-many-ancestors
class EventView(PermissionRequiredMixin, TemplateView, EventContextMixin):
    """
    Class for rendering the events form
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.view_events"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "events/event_form.html"

    # pylint: disable=too-many-locals
    def get(self, request, *args, **kwargs):
        """
        Render event form for HTTP GET requests

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        region = Region.get_current_region(request)
        language = get_object_or_404(region.languages, slug=kwargs.get("language_slug"))

        # get event and event translation objects if they exist, otherwise objects are None
        event_instance = region.events.filter(id=kwargs.get("event_id")).first()
        event_translation_instance = language.event_translations.filter(
            event=event_instance
        ).first()
        recurrence_rule_instance = RecurrenceRule.objects.filter(
            event=event_instance
        ).first()
        poi_instance = region.pois.filter(events=event_instance).first()

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
        context = self.get_context_data(**kwargs)
        return render(
            request,
            self.template_name,
            {
                **context,
                "current_menu_item": "events_form",
                "event_form": event_form,
                "event_translation_form": event_translation_form,
                "recurrence_rule_form": recurrence_rule_form,
                "poi": poi_instance,
                "language": language,
                "languages": region.languages if event_instance else [language],
            },
        )

    # pylint: disable=too-many-locals,too-many-branches
    def post(self, request, **kwargs):
        """
        Save event and ender event form for HTTP POST requests

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit events

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        region = Region.get_current_region(request)
        language = Language.objects.get(slug=kwargs.get("language_slug"))
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

        event_form = EventForm(
            data=request.POST,
            files=request.FILES,
            instance=event_instance,
        )
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

            return render(
                request,
                self.template_name,
                {
                    **self.get_context_data(**kwargs),
                    "current_menu_item": "events",
                    "event_form": event_form,
                    "event_translation_form": event_translation_form,
                    "recurrence_rule_form": recurrence_rule_form,
                    "poi": poi,
                    "language": language,
                    "languages": region.languages if event_instance else [language],
                },
            )

        if (
            not event_form.has_changed()
            and not event_translation_form.has_changed()
            and (
                not event_form.cleaned_data["is_recurring"]
                or not recurrence_rule_form.has_changed()
            )
            and poi == event_instance.location
        ):

            messages.info(request, _("No changes detected."))

            return render(
                request,
                self.template_name,
                {
                    **self.get_context_data(**kwargs),
                    "current_menu_item": "events",
                    "event_form": event_form,
                    "event_translation_form": event_translation_form,
                    "recurrence_rule_form": recurrence_rule_form,
                    "poi": poi,
                    "language": language,
                    "languages": region.languages if event_instance else [language],
                },
            )

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
        event_translation = event_translation_form.save(event=event, user=request.user)

        published = event_translation.status == status.PUBLIC
        if not event_instance:
            if published:
                messages.success(
                    request, _("Event was successfully created and published")
                )
            else:
                messages.success(request, _("Event was successfully created"))
        else:
            if not event_translation_instance:
                if published:
                    messages.success(
                        request,
                        _("Event translation was successfully created and published"),
                    )
                else:
                    messages.success(
                        request, _("Event translation was successfully created")
                    )
            else:
                if published:
                    messages.success(request, _("Event was successfully published"))
                else:
                    messages.success(request, _("Event was successfully saved"))

        return redirect(
            "edit_event",
            **{
                "event_id": event.id,
                "region_slug": region.slug,
                "language_slug": language.slug,
            }
        )
