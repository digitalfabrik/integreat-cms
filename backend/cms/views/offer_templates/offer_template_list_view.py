from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...decorators import staff_required
from ...models import OfferTemplate


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class OfferTemplateListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_offer_templates'
    raise_exception = True

    template_name = 'offer_templates/offer_template_list.html'
    base_context = {'current_menu_item': 'offer_templates'}

    def get(self, request, *args, **kwargs):
        offer_templates = OfferTemplate.objects.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'offer_templates': offer_templates
            }
        )
