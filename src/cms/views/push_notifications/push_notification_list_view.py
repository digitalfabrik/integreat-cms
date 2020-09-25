from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...models import Language, Region


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class PushNotificationListView(PermissionRequiredMixin, TemplateView):
    permission_required = "cms.view_push_notifications"
    raise_exception = True

    template_name = "push_notifications/push_notification_list.html"
    base_context = {"current_menu_item": "push_notifications"}

    def get(self, request, *args, **kwargs):
        # current region
        region = Region.get_current_region(request)

        # current language
        language_code = kwargs.get("language_code")
        if language_code:
            language = Language.objects.get(code=language_code)
        elif region.default_language:
            return redirect(
                "push_notifications",
                **{
                    "region_slug": region.slug,
                    "language_code": region.default_language.code,
                }
            )
        else:
            messages.error(
                request,
                _(
                    "Please create at least one language node before creating push notifications."
                ),
            )
            return redirect(
                "language_tree",
                **{
                    "region_slug": region.slug,
                }
            )

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "push_notifications": region.push_notifications.all(),
                "language": language,
                "languages": region.languages,
            },
        )
