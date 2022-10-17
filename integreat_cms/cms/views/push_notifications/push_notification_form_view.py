import logging

from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.forms import inlineformset_factory
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...utils.push_notification_sender import PushNotificationSender
from ...decorators import permission_required
from ...forms import (
    PushNotificationForm,
    PushNotificationTranslationForm,
)
from ...models import Language, PushNotification, PushNotificationTranslation
from ...utils.translation_utils import ugettext_many_lazy as __

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
    extra_context = {"current_menu_item": "push_notifications_form"}

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

        push_notification = PushNotification.objects.filter(
            id=kwargs.get("push_notification_id")
        ).first()

        if push_notification and push_notification.sent_date:
            messages.info(
                request,
                __(
                    _(
                        "This news message has already been sent as push notification to mobile devices."
                    ),
                    _(
                        'Subsequent changes are displayed in the "News" area of the app, but have no effect on the push notification sent.'
                    ),
                ),
            )

        push_notification_form = PushNotificationForm(instance=push_notification)

        num_languages = len(region.active_languages)
        PushNotificationTranslationFormSet = inlineformset_factory(
            parent_model=PushNotification,
            model=PushNotificationTranslation,
            form=PushNotificationTranslationForm,
            min_num=num_languages,
            max_num=num_languages,
        )
        existing_languages = push_notification.languages if push_notification else []
        pnt_formset = PushNotificationTranslationFormSet(
            # The push notification instance to which we want to create translations
            instance=push_notification,
            # Add initial data for all languages which do not yet have a translation
            initial=[
                {"language": language}
                for language in region.active_languages
                if language not in existing_languages
            ],
        )
        # Make title of default language required
        pnt_formset[0].fields["title"].required = True

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "push_notification_form": push_notification_form,
                "pnt_formset": pnt_formset,
                "language": language,
                "languages": region.active_languages,
            },
        )

    # pylint: disable=too-many-branches,too-many-statements
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

        pn_form = PushNotificationForm(
            data=request.POST,
            instance=push_notification_instance,
            additional_instance_attributes={
                "region": region,
            },
        )

        num_languages = len(region.active_languages)
        PushNotificationTranslationFormSet = inlineformset_factory(
            parent_model=PushNotification,
            model=PushNotificationTranslation,
            form=PushNotificationTranslationForm,
            min_num=num_languages,
            max_num=num_languages,
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
                for language in region.active_languages
                if language not in existing_languages
            ],
        )
        # Make title of default language required
        pnt_formset[0].fields["title"].required = True

        if not pn_form.is_valid():
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
        else:
            # Save forms
            pnt_formset.instance = pn_form.save()
            if not push_notification_instance:
                for form in pnt_formset:
                    form.instance.push_notification = pnt_formset.instance
            pnt_formset.save()

            # Add the success message
            if not push_notification_instance:
                messages.success(
                    request,
                    _('News message "{}" was successfully created').format(
                        pn_form.instance
                    ),
                )
            else:
                messages.success(
                    request,
                    _('News message "{}" was successfully saved').format(
                        pn_form.instance
                    ),
                )

            if "submit_send" in request.POST and not pn_form.instance.sent_date:
                if not request.user.has_perm("cms.send_push_notification"):
                    logger.warning(
                        "%r does not have the permission to send %r",
                        request.user,
                        push_notification_instance,
                    )
                    raise PermissionDenied
                try:
                    push_sender = PushNotificationSender(pn_form.instance)
                    if not push_sender.is_valid():
                        messages.error(
                            request,
                            _(
                                "News message cannot be sent because required texts are missing"
                            ),
                        )
                    else:
                        if push_sender.send_all():
                            messages.success(
                                request, _("News message was successfully sent")
                            )
                            pn_form.instance.sent_date = datetime.now()
                            pn_form.instance.save()
                        else:
                            messages.error(request, _("News message could not be sent"))
                except ImproperlyConfigured as e:
                    logger.error(
                        "News message could not be sent due to a configuration error: %s",
                        e,
                    )
                    messages.error(
                        request,
                        _(
                            "News message could not be sent due to a configuration error."
                        ),
                    )

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
                "languages": region.active_languages,
            },
        )
