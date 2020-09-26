from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...models import Region, Language


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class PageTreeView(PermissionRequiredMixin, TemplateView):
    permission_required = "cms.view_pages"
    raise_exception = True

    template = "pages/page_tree.html"
    template_archived = "pages/page_tree_archived.html"
    archived = False

    @property
    def template_name(self):
        return self.template_archived if self.archived else self.template

    def get(self, request, *args, **kwargs):
        # current region
        region_slug = kwargs.get("region_slug")
        region = Region.get_current_region(request)

        # current language
        language_code = kwargs.get("language_code")
        if language_code:
            language = Language.objects.get(code=language_code)
        elif region.default_language:
            return redirect(
                "pages",
                **{
                    "region_slug": region_slug,
                    "language_code": region.default_language.code,
                }
            )
        else:
            messages.error(
                request,
                _("Please create at least one language node before creating pages."),
            )
            return redirect(
                "language_tree",
                **{
                    "region_slug": region_slug,
                }
            )

        if not request.user.has_perm("cms.edit_page"):
            messages.warning(
                request, _("You don't have the permission to edit or create pages.")
            )

        return render(
            request,
            self.template_name,
            {
                "current_menu_item": "pages",
                "pages": region.pages.filter(archived=self.archived),
                "archived_count": region.pages.filter(archived=True).count(),
                "language": language,
                "languages": region.languages,
            },
        )
