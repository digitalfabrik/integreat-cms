from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render

from .region_form import RegionForm
from ...models.region import Region
from ...decorators import staff_required


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class RegionListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_regions'
    raise_exception = True

    template_name = 'regions/list.html'
    base_context = {'current_menu_item': 'regions'}

    def get(self, request, *args, **kwargs):
        regions = Region.objects.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'regions': regions
            }
        )


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class RegionView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_regions'
    raise_exception = True

    template_name = 'regions/region.html'
    base_context = {'current_menu_item': 'regions'}
    region_slug = None

    def get(self, request, *args, **kwargs):
        self.region_slug = self.kwargs.get('region_slug')
        if self.region_slug:
            region = Region.objects.get(slug=self.region_slug)
            form = RegionForm(initial={
                'name': region.name,
                'events_enabled': region.events_enabled,
                'push_notifications_enabled': region.push_notifications_enabled,
                'latitude': region.latitude,
                'longitude': region.longitude,
                'postal_code': region.postal_code,
                'admin_mail': region.admin_mail,
                'statistics_enabled': region.statistics_enabled,
                'matomo_url': region.matomo_url,
                'matomo_token': region.matomo_token,
                'matomo_ssl_verify': region.matomo_ssl_verify,
                'push_notification_channels': ' '.join(region.push_notification_channels),
                'status': region.status,
            })
        else:
            form = RegionForm()
        return render(request, self.template_name, {
            'form': form, **self.base_context})

    def post(self, request, region_slug=None):
        # TODO: error handling
        form = RegionForm(request.POST)
        if form.is_valid():
            if region_slug:
                form.save_region(region_slug=region_slug)
                messages.success(request, _('Region saved successfully.'))
            else:
                form.save_region()
                messages.success(request, _('Region created successfully'))
            # TODO: improve messages
        else:
            messages.error(request, _('Errors have occurred.'))

        return render(request, self.template_name, {
            'form': form, **self.base_context})
