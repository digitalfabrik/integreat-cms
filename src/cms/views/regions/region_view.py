from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import staff_required
from ...forms.regions import RegionForm
from ...models import Region


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class RegionView(PermissionRequiredMixin, TemplateView):
    permission_required = "cms.manage_regions"
    raise_exception = True

    template_name = "regions/region_form.html"
    base_context = {"current_menu_item": "regions"}

    def get(self, request, *args, **kwargs):

        region_instance = Region.objects.filter(slug=kwargs.get("region_slug")).first()

        form = RegionForm(instance=region_instance)

        return render(request, self.template_name, {"form": form, **self.base_context})

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):

        region_instance = Region.objects.filter(slug=kwargs.get("region_slug")).first()

        form = RegionForm(request.POST, instance=region_instance)

        # TODO: error handling
        if not form.is_valid():
            messages.error(request, _("Errors have occurred."))
            return render(
                request, self.template_name, {"form": form, **self.base_context}
            )

        if not form.has_changed():
            messages.info(request, _("No changes detected."))
            return render(
                request, self.template_name, {"form": form, **self.base_context}
            )

        region = form.save()

        if region_instance:
            messages.success(request, _("Region was saved successfully"))
        else:
            messages.success(request, _("Region was created successfully"))

        return redirect(
            "edit_region",
            **{
                "region_slug": region.slug,
            }
        )
