from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from ...decorators import staff_required
from ...forms.offer_templates import OfferTemplateForm
from ...models import OfferTemplate


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class OfferTemplateView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_offer_templates'
    raise_exception = True

    template_name = 'offer_templates/offer_template_form.html'
    base_context = {'current_menu_item': 'offer_templates'}

    def get(self, request, *args, **kwargs):
        offer_template_id = self.kwargs.get('offer_template_id', None)
        if offer_template_id:
            offer_template = OfferTemplate.objects.get(id=offer_template_id)
            form = OfferTemplateForm(instance=offer_template)
        else:
            form = OfferTemplateForm()
        return render(request, self.template_name, {
            'form': form,
            **self.base_context
        })

    def post(self, request, offer_template_id=None):

        if offer_template_id:
            offer_template = OfferTemplate.objects.get(id=offer_template_id)
            form = OfferTemplateForm(request.POST, instance=offer_template)
            success_message = _('Offer template saved successfully')
        else:
            form = OfferTemplateForm(request.POST)
            success_message = _('Offer template created successfully')

        if form.is_valid():
            messages.success(request, success_message)
            offer_template = form.save()
            return redirect('edit_offer_template', **{
                'offer_template_id': offer_template.id
            })

        messages.error(request, _('Errors have occurred.'))
        # TODO: improve messages
        return render(request, self.template_name, {
            'form': form,
            **self.base_context
        })
