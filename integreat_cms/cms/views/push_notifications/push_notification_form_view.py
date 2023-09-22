import logging
from copy import deepcopy
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.forms import inlineformset_factory
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.html import mark_safe
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from ....firebase_api.firebase_api_client import FirebaseApiClient
from ...decorators import permission_required
from ...forms import PushNotificationForm, PushNotificationTranslationForm
from ...models import Language, PushNotification, PushNotificationTranslation
from ...utils.translation_utils import gettext_many_lazy as __

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
    def get(self, request, *args, **kwargs):
        r"""
        Open form for creating or editing a push notification

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
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
        # Make title of default language required
        pnt_formset[0].fields["title"].required = True

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

    # pylint: disable=too-many-branches, too-many-statements
    def post(self, request, *args, **kwargs):
        r"""
        Save and show form for creating or editing a push notification. Send push notification
        if asked for by user.

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to send push notifications

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
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
        # Make title of default language required
        pnt_formset[0].fields["title"].required = True

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
        elif not pn_form.is_valid():
            # Add error messages
            pn_form.add_error_messages(request)
        elif not pnt_formset.is_valid():
            # Add non-form errors
            for error in pnt_formset.non_form_errors():
                messages.error(request, _(error))
                logger.debug(
                    "Error when validating push notification formset: %r", error
                )
            # Add form error messages
            for form in pnt_formset:
                if not form.is_valid():
                    form.add_error_messages(request)
        elif set(pn_form.cleaned_data["regions"]).difference(request.available_regions):
            logger.warning(
                "%r is not allowed to post news to %r (allowed regions: %r)",
                request.user,
                pn_form.cleaned_data["regions"],
                request.available_regions,
            )
            raise PermissionDenied
        else:
            # Save forms
            pnt_formset.instance = pn_form.save()
            if not push_notification_instance:
                for form in pnt_formset:
                    form.instance.push_notification = pnt_formset.instance
            pnt_formset.save()

            # Add the success message
            if not push_notification_instance:
                if pn_form.cleaned_data["is_template"]:
                    messages.success(
                        request,
                        _('Template "{}" was successfully created').format(
                            pn_form.cleaned_data["template_name"]
                        ),
                    )
                else:
                    messages.success(
                        request,
                        _('News "{}" was successfully created').format(
                            pn_form.instance
                        ),
                    )
            else:
                if pn_form.cleaned_data["is_template"]:
                    messages.success(
                        request,
                        _('Template "{}" was successfully saved').format(
                            pn_form.cleaned_data["template_name"]
                        ),
                    )
                else:
                    messages.success(
                        request,
                        _('News "{}" was successfully saved').format(pn_form.instance),
                    )

            # The submit_send submit button is used in 2 cases:
            # 1. send a push notification
            # 2. create push notifiaction from template
            if "submit_send" in request.POST and not pn_form.instance.sent_date:
                if not request.user.has_perm("cms.send_push_notification"):
                    logger.warning(
                        "%r does not have the permission to send %r",
                        request.user,
                        push_notification_instance,
                    )
                    raise PermissionDenied

                try:
                    push_sender = FirebaseApiClient(pn_form.instance)
                    if not push_sender.is_valid():
                        messages.error(
                            request,
                            _("News cannot be sent because required texts are missing"),
                        )
                    elif pn_form.instance.scheduled_send_date:
                        pn_form.instance.draft = False
                        pn_form.instance.save()
                    elif pn_form.instance.is_template:
                        new_message = deepcopy(pn_form.instance)
                        new_message.pk = None
                        new_message.is_template = False
                        new_message.draft = True
                        new_message.save()
                        new_message.regions.set(pn_form.instance.regions.all())
                        for translation in pn_form.instance.translations.all():
                            new_translation = deepcopy(translation)
                            new_translation.push_notification = new_message
                            new_translation.pk = None
                            new_translation.save()
                        return redirect(
                            "edit_push_notification",
                            **{
                                "push_notification_id": new_message.pk,
                                "region_slug": region.slug,
                                "language_slug": language.slug,
                            },
                        )
                    elif push_sender.send_all():
                        messages.success(request, _("News was successfully sent"))
                        pn_form.instance.sent_date = datetime.now()
                        pn_form.instance.draft = False
                        pn_form.instance.save()
                    else:
                        messages.error(request, _("News cannot be sent"))
                except ImproperlyConfigured as e:
                    logger.error(
                        "News cannot be sent due to a configuration error: %s",
                        e,
                    )
                    messages.error(
                        request,
                        _("News cannot be sent due to a configuration error."),
                    )
            else:
                pn_form.instance.draft = True
                pn_form.instance.save()

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


def extract_pn_details(request, push_notification, sort_for_region=None):
    r"""
    Save and show form for creating or editing a push notification. Send push notification
    if asked for by user.

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param push_notification: The existing PushNotification or None
    :type push_notification: ~integreat_cms.cms.models.push_notifications.push_notification.PushNotification

    :param sort_for_region: Region for which to keep sorting order (according to language tree)
    :type sort_for_region: ~integreat_cms.cms.models.regions.region.Region

    :return: A dict containing
        * `all_regions`, a list of all :class:`~integreat_cms.cms.models.regions.region.Region` objects of the existing PushNotification (or the current region, if it doesn't exist yet),
        * `other_regions`, the sublist of `all_regions` which the current user doesn't have access to,
        * `all_languages`, a cumulative list of all active languages across all regions in `all_regions` and
        * `disable_edit`, a boolean determining whether the user should be able to edit the PushNotification given his status (superuser, staff) and the vacancy of `other_regions`.
    :rtype: dict
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
            list(all_languages),
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
