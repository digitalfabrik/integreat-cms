from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from cms.decorators import staff_required
from ..models import CMSCache
from ..utils import get_name


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class CMSCacheListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.change_user'
    raise_exception = True

    template_name = 'list.html'
    base_context = {'current_menu_item': 'federation'}

    def get(self, request, *args, **kwargs):
        cms_caches = CMSCache.objects.all()
        name = get_name()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'cms_caches': cms_caches,
                'name': name,
            }
        )
