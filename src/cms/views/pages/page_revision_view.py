from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...constants import status
from ...decorators import region_permission_required
from ...models import Region, Language


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class PageRevisionView(PermissionRequiredMixin, TemplateView):
    """
    View for browsing the page revisions and restoring old page revisions
    """

    permission_required = "cms.view_pages"
    raise_exception = True

    template_name = "pages/page_revisions.html"
    base_context = {"current_menu_item": "pages"}

    def get(self, request, *args, **kwargs):

        region = Region.objects.get(slug=kwargs.get("region_slug"))
        page = region.pages.get(pk=kwargs.get("page_id"))
        language = Language.objects.get(code=kwargs.get("language_code"))

        page_translations = page.translations.filter(language=language)

        if not page_translations.exists():
            return redirect(
                "edit_page",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_code": language.code,
                }
            )

        if not request.user.has_perm("cms.edit_page", page):
            messages.warning(
                request,
                _("You don't have the permission to restore revisions of this page."),
            )

        selected_revision = page_translations.filter(
            version=kwargs.get("selected_revision", page_translations.count())
        )

        if not selected_revision.exists():
            messages.error(request, _("This revision does not exist."))
            return redirect(
                "page_revisions",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_code": language.code,
                }
            )

        if page.archived:
            messages.warning(
                request,
                _("You cannot restore revisions of this page because it is archived."),
            )

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "page": page,
                "page_translations": page_translations,
                "api_revision": page_translations.filter(status=status.PUBLIC).first(),
                "selected_revision": selected_revision.first(),
                "language": language,
            },
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):

        region = Region.objects.get(slug=kwargs.get("region_slug"))
        page = region.pages.get(pk=kwargs.get("page_id"))

        if not request.user.has_perm("cms.edit_page", page):
            raise PermissionDenied

        language = Language.objects.get(code=kwargs.get("language_code"))

        revision = page.translations.filter(
            language=language, version=request.POST.get("revision")
        ).first()

        if not revision:
            messages.error(request, _("This revision does not exist."))
            return redirect(
                "page_revisions",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_code": language.code,
                }
            )

        current_revision = page.get_translation(language.code)

        if (
            revision.slug == current_revision.slug
            and revision.title == current_revision.title
            and revision.text == current_revision.text
        ):
            messages.error(
                request,
                _(
                    "This revision is identical to the current version of this translation."
                ),
            )
            return redirect(
                "page_revisions",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_code": language.code,
                }
            )

        revision.pk = None
        revision.version = current_revision.version + 1

        if request.POST.get("submit_draft"):
            revision.status = status.DRAFT
        elif request.POST.get("submit_review"):
            revision.status = status.REVIEW
        elif request.POST.get("submit_public"):
            if not request.user.has_perm("cms.publish_page", page):
                raise PermissionDenied
            revision.status = status.PUBLIC

        revision.save()

        messages.success(request, _("The revision has been successfully restored."))

        page_translations = page.translations.filter(language=language)

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "page": page,
                "page_translations": page_translations,
                "api_revision": page_translations.filter(status=status.PUBLIC).first(),
                "selected_revision": revision,
                "language": language,
            },
        )
