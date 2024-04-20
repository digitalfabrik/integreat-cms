from __future__ import annotations

import logging
from copy import deepcopy
from datetime import datetime
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.forms import inlineformset_factory
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.formats import localize
from django.utils.html import mark_safe
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ....firebase_api.firebase_api_client import FirebaseApiClient
from ...decorators import permission_required
from ...forms import PushNotificationForm, PushNotificationTranslationForm
from ...models import Language, PushNotification, PushNotificationTranslation
from ...utils.translation_utils import gettext_many_lazy as __

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

    from integreat_cms.cms.models.regions.region import Region

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_pushnotification"), name="dispatch")
@method_decorator(permission_required("cms.change_pushnotification"), name="post")
class PushNotificationFormView(TemplateView):
    """
    Class that handles HTTP POST and GET requests for editing push notifications
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "push_notifications/push_notification_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {
        "current_menu_item": "push_notifications_form",
        "schedule_interval": settings.FCM_SCHEDULE_INTERVAL_MINUTES,
    }

    # pylint: disable=too-many-locals
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Open form for creating or editing a push notification

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        region = request.region

        if not settings.FCM_ENABLED:
            messages.error(
                request,
                _("Push notifications are disabled."),
            )
            return redirect("dashboard", **{"region_slug": region.slug})

        if not region.push_notifications_enabled:
            messages.error(
                request,
                _("Push notifications are disabled in this region."),
            )
            return redirect("dashboard", **{"region_slug": region.slug})

        language = region.get_language_or_404(
            kwargs.get("language_slug"), only_active=True
        )

        push_notification_id = kwargs.get("push_notification_id")
        push_notification = (
            region.push_notifications.get(id=push_notification_id)
            if push_notification_id
            else None
        )

        details = extract_pn_details(request, push_notification, sort_for_region=region)
        not_accessible_regions_warning = None

        if push_notification:
            if push_notification.sent_date:
                messages.info(
                    request,
                    __(
                        _(
                            "This news has already been sent as push notification to mobile devices."
                        ),
                        _(
                            'Subsequent changes are displayed in the "News" area of the app, but have no effect on the push notification sent.'
                        ),
                    ),
                )
            if details["disable_edit"]:
                not_accessible_regions_warning = mark_safe(
                    __(
                        _("You are not allowed to edit this news."),
                        _(
                            "This news belongs to regions you don't have access to: {}."
                        ).format(", ".join(map(str, details["other_regions"]))),
                        _(
                            "Please ask a person responsible for all regions or contact an administrator."
                        ),
                    )
                )
                messages.warning(
                    request,
                    not_accessible_regions_warning,
                )

        push_notification_form = PushNotificationForm(
            regions=request.available_regions,
            selected_regions=[region],
            instance=push_notification,
            disabled=details["disable_edit"],
            template=("template" in request.GET),
        )

        PushNotificationTranslationFormSet = inlineformset_factory(
            parent_model=PushNotification,
            model=PushNotificationTranslation,
            form=PushNotificationTranslationForm,
            min_num=len(details["all_languages"]),
            max_num=len(details["all_languages"]),
        )
        existing_languages = push_notification.languages if push_notification else []
        pnt_formset = PushNotificationTranslationFormSet(
            # The push notification instance to which we want to create translations
            instance=push_notification,
            # Add initial data for all languages which do not yet have a translation
            initial=[
                {"language": language}
                for language in details["all_languages"]
                if language not in existing_languages
            ],
        )

        if details["disable_edit"]:
            # Mark fields disabled when push notification was already sent
            for formset in pnt_formset:
                for field in formset.fields.values():
                    field.disabled = True

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "push_notification_form": push_notification_form,
                "pnt_formset": pnt_formset,
                "language": language,
                "languages": details["all_languages"],
                "not_accessible_regions_warning": not_accessible_regions_warning,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Save and show form for creating or editing a push notification. Send push notification
        if asked for by user.

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to send push notifications
        :raises NotImplementedError: If no valid submit button was clicked

        :return: The rendered template response
        """

        region = request.region
        language = Language.objects.get(slug=kwargs.get("language_slug"))

        push_notification_instance = PushNotification.objects.filter(
            id=kwargs.get("push_notification_id")
        ).first()

        if not request.user.has_perm("cms.change_pushnotification"):
            logger.warning(
                "%r tried to edit %r",
                request.user,
                push_notification_instance,
            )
            raise PermissionDenied

        details = extract_pn_details(
            request, push_notification_instance, sort_for_region=region
        )

        pn_form = PushNotificationForm(
            data=request.POST,
            instance=push_notification_instance,
            additional_instance_attributes={
                "region": region,
            },
            regions=request.available_regions,
            selected_regions=[region],
            disabled=details["disable_edit"],
        )

        PushNotificationTranslationFormSet = inlineformset_factory(
            parent_model=PushNotification,
            model=PushNotificationTranslation,
            form=PushNotificationTranslationForm,
            min_num=len(details["all_languages"]),
            max_num=len(details["all_languages"]),
        )
        existing_languages = (
            push_notification_instance.languages if push_notification_instance else []
        )
        pnt_formset = PushNotificationTranslationFormSet(
            data=request.POST,
            # The push notification instance to which we want to create translations
            instance=push_notification_instance,
            # Add initial data for all languages which do not yet have a translation
            initial=[
                {"language": language}
                for language in details["all_languages"]
                if language not in existing_languages
            ],
        )

        if validate_forms(request, details, pn_form, pnt_formset):
            save_forms(push_notification_instance, pn_form, pnt_formset)
            # Add the success message
            action = _("updated") if push_notification_instance else _("created")
            if pn_form.instance.is_template:
                messages.success(
                    request,
                    _('Template "{}" was successfully {}').format(
                        pn_form.instance.template_name, action
                    ),
                )
            else:
                messages.success(
                    request,
                    _('News "{}" was successfully {}').format(pn_form.instance, action),
                )

            success = True

            if "submit_draft" in request.POST:
                pn_form.instance.draft = True
                pn_form.instance.save()
            elif "submit_update" in request.POST:
                pn_form.instance.draft = False
                pn_form.instance.save()
            elif "create_from_template" in request.POST:
                if new_push_notification := create_from_template(request, pn_form):
                    return redirect(
                        "edit_push_notification",
                        **{
                            "push_notification_id": new_push_notification.pk,
                            "region_slug": region.slug,
                            "language_slug": language.slug,
                        },
                    )
                success = False
            elif "submit_schedule" in request.POST:
                success = send_pn(request, pn_form, schedule=True)
            elif "submit_send" in request.POST:
                success = send_pn(request, pn_form)
            else:
                raise NotImplementedError(
                    "One of the following keys is required in POST data: 'submit_draft', 'submit_update', 'create_from_template', 'submit_schedule', 'submit_send'"
                )

            if success:
                # Redirect to the edit page
                return redirect(
                    "edit_push_notification",
                    **{
                        "push_notification_id": pn_form.instance.id,
                        "region_slug": region.slug,
                        "language_slug": language.slug,
                    },
                )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "push_notification_form": pn_form,
                "pnt_formset": pnt_formset,
                "language": language,
                "languages": details["all_languages"],
            },
        )


def validate_forms(
    request: HttpRequest,
    details: dict,
    pn_form: PushNotificationForm,
    pnt_formset: Any,
) -> bool:
    """
    Validates the forms and returns `True` iff no errors occurred.
    :param request: The request
    :param details: The push notification details
    :param pn_form: The push notification form
    :param pnt_formset: The push notification translation formset
    :return: whether verification was successful
    """
    if details["disable_edit"]:
        not_accessible_regions_warning = __(
            _(
                "This news is also assigned to regions you don't have access to: {}."
            ).format(", ".join(map(str, details["other_regions"]))),
            _("Thus you cannot edit or delete this news."),
            _(
                "Please ask the one responsible for all of these regions or contact an administrator."
            ),
        )
        messages.error(
            request,
            not_accessible_regions_warning,
        )
        return False

    if not pn_form.is_valid():
        # Add error messages
        pn_form.add_error_messages(request)
        return False

    # Make the title of the default language of each region required.
    # This guarantees that there is always a push notification in the default language available, even if the regions
    # of the push notification get changed later on.
    pn_regions = pn_form.cleaned_data["regions"]
    required_languages = {region.default_language.id for region in pn_regions}
    for form in pnt_formset:
        if int(form["language"].value()) in required_languages:
            form.fields["title"].required = True

    if not pnt_formset.is_valid():
        # Add non-form errors
        for error in pnt_formset.non_form_errors():
            messages.error(request, _(error))
        # Add form error messages
        for form in pnt_formset:
            if not form.is_valid():
                form.add_error_messages(request)
        return False

    if set(pn_regions).difference(request.available_regions):
        logger.warning(
            "%r is not allowed to post news to %r (allowed regions: %r)",
            request.user,
            pn_regions,
            request.available_regions,
        )
        raise PermissionDenied

    return True


def save_forms(
    instance: PushNotification, pn_form: PushNotificationForm, pnt_formset: Any
) -> None:
    """
    Saves the forms
    :param instance: The push notification instance
    :param pn_form: The push notification form
    :param pnt_formset: The push notification translation formset
    """
    pnt_formset.instance = pn_form.save()
    if not instance:
        for form in pnt_formset:
            form.instance.push_notification = pnt_formset.instance
    pnt_formset.save()


def create_from_template(
    request: HttpRequest, pn_form: PushNotificationForm
) -> PushNotification | None:
    """
    Create a push notification from a template

    :param request: The current request
    :param pn_form: The push notification form
    :return: The new created push notification object
    """
    if not pn_form.instance.is_template:
        messages.error(
            request,
            _('News "{}" is not a template').format(pn_form.instance),
        )
        return None

    new_push_notification = deepcopy(pn_form.instance)
    new_push_notification.pk = None
    new_push_notification.is_template = False
    new_push_notification.template_name = None
    new_push_notification.draft = True
    new_push_notification.save()
    new_push_notification.regions.set(pn_form.instance.regions.all())
    for translation in pn_form.instance.translations.all():
        new_translation = deepcopy(translation)
        new_translation.push_notification = new_push_notification
        new_translation.pk = None
        new_translation.save()
    messages.success(
        request,
        __(
            _('News "{}" was successfully created from template "{}".').format(
                new_push_notification, pn_form.instance.template_name
            ),
            _("In the next step, the news can now be sent."),
        ),
    )
    return new_push_notification


# pylint: disable=too-many-return-statements
def send_pn(
    request: HttpRequest, pn_form: PushNotificationForm, schedule: bool = False
) -> bool:
    """
    Send (or schedule) a push notification

    :param request: The current request
    :param pn_form: The push notification form
    :param schedule: Whether the message should be scheduled instead of sent directly
    :raises ~django.core.exceptions.PermissionDenied: When the user does not have the permission to send notifications

    :return: Whether sending (or scheduling) was successful
    """
    if not request.user.has_perm("cms.send_push_notification"):
        logger.warning(
            "%r does not have the permission to send %r",
            request.user,
            pn_form.instance,
        )
        raise PermissionDenied

    if pn_form.instance.sent_date:
        messages.error(
            request,
            _('News "{}" was already sent on {}').format(
                pn_form.instance, localize(localtime(pn_form.instance.sent_date))
            ),
        )
        return False

    try:
        push_sender = FirebaseApiClient(pn_form.instance)
    except ImproperlyConfigured as e:
        logger.error(
            "News could not be sent due to a configuration error: %s",
            e,
        )
        messages.error(
            request,
            _('News "{}" could not be sent due to a configuration error.').format(
                pn_form.instance
            ),
        )
        return False
    if not push_sender.is_valid():
        messages.error(
            request,
            _('News "{}" cannot be sent because required texts are missing').format(
                pn_form.instance
            ),
        )
        return False
    if schedule:
        if not pn_form.instance.scheduled_send_date:
            messages.error(
                request,
                _('News "{}" cannot be scheduled because the date is missing').format(
                    pn_form.instance
                ),
            )
            return False
        pn_form.instance.draft = False
        pn_form.instance.save()
        messages.success(
            request,
            _('News "{}" was successfully scheduled for {}').format(
                pn_form.instance,
                localize(localtime(pn_form.instance.scheduled_send_date)),
            ),
        )
        return True
    if not push_sender.send_all():
        messages.error(
            request,
            __(
                _('News "{}" could not be sent.').format(pn_form.instance),
                _("Please try again later or contact an administrator."),
            ),
        )
        return False
    pn_form.instance.sent_date = datetime.now()
    pn_form.instance.draft = False
    pn_form.instance.save()
    messages.success(
        request, _('News "{}" was successfully sent').format(pn_form.instance)
    )
    return True


def extract_pn_details(
    request: HttpRequest,
    push_notification: PushNotification | None,
    sort_for_region: Region | None = None,
) -> dict[str, Any]:
    r"""
    Save and show form for creating or editing a push notification. Send push notification
    if asked for by user.

    :param request: Object representing the user call
    :param push_notification: The existing PushNotification or None
    :param sort_for_region: Region for which to keep sorting order (according to language tree)
    :return: A dict containing
        * `all_regions`, a list of all :class:`~integreat_cms.cms.models.regions.region.Region` objects of the existing PushNotification (or the current region, if it doesn't exist yet),
        * `other_regions`, the sublist of `all_regions` which the current user doesn't have access to,
        * `all_languages`, a cumulative list of all active languages across all regions in `all_regions` and
        * `disable_edit`, a boolean determining whether the user should be able to edit the PushNotification given his status (superuser, staff) and the vacancy of `other_regions`.
    """
    all_regions = (
        push_notification.regions.all() if push_notification else [request.region]
    )
    other_regions = list(set(all_regions).difference(request.available_regions))
    all_languages = Language.objects.filter(
        language_tree_nodes__region__in=all_regions, language_tree_nodes__active=True
    ).distinct()

    if sort_for_region is not None:
        act = sort_for_region.active_languages
        all_languages = sorted(
            all_languages,
            key=lambda x: act.index(x) if x in act else 1,
        )
    disable_edit = bool(
        not request.user.is_superuser and not request.user.is_staff and other_regions
    )
    return {
        "all_regions": all_regions,
        "other_regions": other_regions,
        "all_languages": all_languages,
        "disable_edit": disable_edit,
    }
