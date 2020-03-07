from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import staff_required
from ...models import Language


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class LanguageListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_languages'
    raise_exception = True

    template_name = 'languages/language_list.html'
    base_context = {'current_menu_item': 'languages'}

    def get(self, request, *args, **kwargs):
        languages = Language.objects.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'languages': languages
            }
        )
