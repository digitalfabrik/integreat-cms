from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...forms.media.directory_form import DirectoryForm
from ...models import Region, Directory


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class CreateDirectoryView(TemplateView):
    template_name = "media/directory_form.html"
    base_context = {"current_menu_item": "media"}

    def get(self, request, *args, **kwargs):
        slug = kwargs.get("region_slug")
        region = Region.objects.get(slug=slug)
        directory_id = kwargs.get("directory_id")
        form = DirectoryForm()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "form": form,
                "region_slug": region.slug,
                "directory_id": directory_id,
            },
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        slug = kwargs.get("region_slug")
        region = Region.objects.get(slug=slug)
        directory_id = int(kwargs.get("directory_id"))
        if directory_id != 0:
            parent_directory = Directory.objects.get(id=directory_id)
        else:
            parent_directory = None

        directory = Directory()
        directory.region = region
        directory.parent = parent_directory
        form = DirectoryForm(request.POST, instance=directory)
        if form.is_valid():
            form.save()
            return redirect(
                "media", **{"region_slug": region.slug, "directory_id": directory_id}
            )

        messages.error(request, _("Errors have occurred."))

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "region_slug": region.slug,
                "directory_id": directory_id,
                **self.base_context,
            },
        )
