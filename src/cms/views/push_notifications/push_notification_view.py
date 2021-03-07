from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.forms import modelformset_factory

from .push_notification_sender import PushNotificationSender
from ...decorators import region_permission_required
from ...forms import (
    PushNotificationForm,
    PushNotificationTranslationForm,
)
from ...models import Language, PushNotification, PushNotificationTranslation, Region


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class PushNotificationView(PermissionRequiredMixin, TemplateView):
    """
    Class that handles HTTP POST and GET requests for editing push notifications
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.view_push_notifications"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "push_notifications/push_notification_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "push_notifications_form"}

    def get(self, request, *args, **kwargs):
        """
        Open form for creating or editing a push notification

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit push notifications

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        push_notification = PushNotification.objects.filter(
            id=kwargs.get("push_notification_id")
        ).first()
        region = Region.get_current_region(request)
        language = Language.objects.get(slug=kwargs.get("language_slug"))
        num_languages = len(region.languages)
        if push_notification is not None:
            pn_form = PushNotificationForm(instance=push_notification)
            PNTFormset = modelformset_factory(
                PushNotificationTranslation,
                form=PushNotificationTranslationForm,
                max_num=num_languages,
                extra=3,
            )
            pnt_formset = PNTFormset(
                queryset=PushNotificationTranslation.objects.filter(
                    push_notification=pn_form.instance
                ).order_by("language")
            )
        else:
            pn_form = PushNotificationForm()
            initial_data = []
            for lang in region.languages:
                lang_data = {"language": lang.id}
                initial_data.append(lang_data)
            PNTFormset = modelformset_factory(
                PushNotificationTranslation,
                form=PushNotificationTranslationForm,
                max_num=num_languages,
                extra=num_languages,
            )
            pnt_formset = PNTFormset(
                queryset=PushNotificationTranslation.objects.none(),
                initial=initial_data,
            )

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "push_notification": push_notification,
                "push_notification_form": pn_form,
                "pnt_formset": pnt_formset,
                "language": language,
                "languages": region.languages,
            },
        )

    # pylint: disable=too-many-branches,unused-argument
    def post(self, request, *args, **kwargs):
        """
        Save and show form for creating or editing a push notification. Send push notification
        if asked for by user.

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit push notifications

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        push_notification = PushNotification.objects.filter(
            id=kwargs.get("push_notification_id")
        ).first()

        if not request.user.has_perm("cms.edit_push_notifications"):
            raise PermissionDenied

        region = Region.get_current_region(request)
        language = Language.objects.get(slug=kwargs.get("language_slug"))
        num_languages = len(region.languages)

        PushNewsFormset = modelformset_factory(
            PushNotificationTranslation,
            form=PushNotificationTranslationForm,
            max_num=num_languages,
        )
        pnt_formset = PushNewsFormset(request.POST)
        pn_form = PushNotificationForm(request.POST, instance=push_notification)
        if pn_form.is_valid():
            push_notification = pn_form.save(commit=False)
            push_notification.region = region
            push_notification.save()

            if pnt_formset.is_valid():
                pnt_formset.save(commit=False)
                for form in pnt_formset:
                    form.instance.push_notification = push_notification
                    form.save()
                messages.success(request, _("Push Notification saved"))
        else:
            messages.error(request, _("Error while saving Push Notification"))

        if "submit_send" in request.POST:
            if not request.user.has_perm("cms.send_push_notifications"):
                raise PermissionDenied
            push_sender = PushNotificationSender(push_notification)
            if push_sender.is_valid():
                if push_sender.send_all():
                    messages.success(request, _("Push Notification send successfully"))
                    push_notification.sent_date = datetime.now()
                    push_notification.save()
                else:
                    messages.error(request, _("Error while sending Push Notification"))
            else:
                messages.warning(
                    request, _("Required Push Notification texts are missing")
                )

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "push_notification": push_notification,
                "push_notification_form": pn_form,
                "pnt_formset": pnt_formset,
                "language": language,
                "languages": region.languages,
            },
        )
