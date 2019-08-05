from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from .push_notification_sender import PushNotificationSender
from .push_notification_form import PushNotificationForm, PushNotificationTranslationForm
from ...models.push_notification import PushNotification, PushNotificationTranslation
from ...models.language import Language
from ...models.region import Region
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class PushNotificationListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.view_push_notifications'
    raise_exception = True

    template_name = 'push_notifications/list.html'
    base_context = {'current_menu_item': 'push_notifications'}

    def get(self, request, *args, **kwargs):
        # current region
        region = Region.objects.get(slug=kwargs.get('region_slug'))

        # current language
        language_code = kwargs.get('language_code', None)
        if language_code:
            language = Language.objects.get(code=language_code)
        elif region.default_language:
            return redirect('push_notifications', **{
                'region_slug': region.slug,
                'language_code': region.default_language.code,
            })
        else:
            messages.error(
                request,
                _('Please create at least one language node before creating push notifications.')
            )
            return redirect('language_tree', **{
                'region_slug': region.slug,
            })

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'push_notifications': region.push_notifications.all(),
                'language': language,
                'languages': region.languages,
            }
        )


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class PushNotificationView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.view_push_notifications'
    raise_exception = True

    template_name = 'push_notifications/push_notification.html'
    base_context = {'current_menu_item': 'push_notifications'}
    push_sender = PushNotificationSender()

    def get(self, request, *args, **kwargs):
        push_notification = PushNotification.objects.filter(id=kwargs.get('push_notification_id')).first()
        region = Region.objects.get(slug=kwargs.get('region_slug'))
        language = Language.objects.get(code=kwargs.get('language_code'))
        if push_notification:
            push_notification_form = PushNotificationForm(instance=push_notification)
            push_notification_translation = PushNotificationTranslation.objects.filter(
                push_notification=push_notification,
                language=language
            )
            if push_notification_translation.exists():
                push_notification_translation_form = PushNotificationTranslationForm(
                    instance=push_notification_translation.first()
                )
            else:
                push_notification_translation_form = PushNotificationTranslationForm()
        else:
            push_notification_form = PushNotificationForm()
            push_notification_translation_form = PushNotificationTranslationForm()
        return render(request, self.template_name, {
            **self.base_context,
            'push_notification': push_notification,
            'push_notification_form': push_notification_form,
            'push_notification_translation_form': push_notification_translation_form,
            'language': language,
            'languages': region.languages,
        })

    # pylint: disable=R0912
    def post(self, request, *args, **kwargs):

        if not request.user.has_perm('cms.edit_push_notifications'):
            raise PermissionDenied

        if 'submit_send' in request.POST:
            if not request.user.has_perm('cms.send_push_notifications'):
                raise PermissionDenied

        region = Region.objects.get(slug=kwargs.get('region_slug'))
        language = Language.objects.get(code=kwargs.get('language_code'))

        # At first check if push notification exists already
        push_notification = PushNotification.objects.filter(id=kwargs.get('push_notification_id')).first()
        if push_notification:
            push_notification_form = PushNotificationForm(request.POST, instance=push_notification)
            success_message = _('Push notification saved successfully.')
        else:
            push_notification_form = PushNotificationForm(request.POST)
            success_message = _('Push notification created successfully.')

        # Then check if translation in current language already exists
        push_notification_translation = PushNotificationTranslation.objects.filter(
            push_notification=push_notification,
            language=language
        )
        if push_notification_translation.exists():
            push_notification_translation_form = PushNotificationTranslationForm(
                request.POST,
                instance=push_notification_translation.first()
            )
        else:
            push_notification_translation_form = PushNotificationTranslationForm(request.POST)

        # If both forms are valid, save them
        if push_notification_form.is_valid() and push_notification_translation_form.is_valid():
            if push_notification:
                push_notification = push_notification_form.save()
            else:
                # The push notification cannot be created directly, because it has a required foreign key to region
                # (which has to be set indirectly before saving)
                push_notification = push_notification_form.save(commit=False)
                push_notification.region = region
                push_notification.save()
            if push_notification_translation:
                push_notification_translation_form.save()
            else:
                # The push notification translation cannot be created directly,
                # because it has a required foreign key to push notifications and languages
                # (which has to be set indirectly before saving)
                push_notification_translation = push_notification_translation_form.save(commit=False)
                push_notification_translation.push_notification = push_notification
                push_notification_translation.language = language
                push_notification_translation.save()
            messages.success(request, success_message)

            # Check if Save button has been clicked
            if push_notification_form.data.get('submit_send'):

                push_sent = self.push_sender.send(region.slug, push_notification.channel, push_notification_translation.title,
                                                  push_notification_translation.text, language.code)

                if push_sent:
                    push_notification.sent_date = timezone.now()
                    push_notification.save()
                    messages.success(request, _('Push notification was successfully sent.'))
                else:
                    messages.error(request, _('Error occurred sending the push notification'))

        else:
            messages.error(request, _('Errors have occurred.'))

        return render(request, self.template_name, {
            **self.base_context,
            'push_notification': push_notification,
            'push_notification_form': push_notification_form,
            'push_notification_translation_form': push_notification_translation_form,
            'language': language,
            'languages': region.languages,
        })
