from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...models import Accommodation, Language, Region


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class AccommodationListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_accommodations'
    raise_exception = True

    template = 'accommodations/accommodation_list.html'
    template_archived = 'accommodations/accommodation_list_archived.html'
    archived = False

    @property
    def template_name(self):
        return self.template_archived if self.archived else self.template

    def get(self, request, *args, **kwargs):
        # current region
        region_slug = kwargs.get('region_slug')
        region = Region.objects.get(slug=region_slug)

        # current language
        language_code = kwargs.get('language_code', None)
        if language_code:
            language = Language.objects.get(code=language_code)
        elif region.default_language:
            return redirect('accommodations', **{
                'region_slug': region_slug,
                'language_code': region.default_language.code,
            })
        else:
            messages.error(
                request,
                _('Please create at least one language node before creating Accommodations.')
            )
            return redirect('language_tree', **{
                'region_slug': region_slug,
            })

        if not request.user.has_perm('cms.edit_accommodations'):
            messages.warning(request, _("You don't have the permission to edit or create Accommodations."))

        if language != region.default_language:
            messages.warning(
                request,
                _("You can only create Accommodations in the default language (%(language)s).")
                % {'language': region.default_language.translated_name}
            )

        return render(
            request,
            self.template_name,
            {
                'current_menu_item': 'accommodations',
                'accommodations': Accommodation.objects.filter(region=region, archived=self.archived),
                'archived_count': Accommodation.objects.filter(region=region, archived=True).count(),
                'language': language,
                'languages': region.languages,
            }
        )
