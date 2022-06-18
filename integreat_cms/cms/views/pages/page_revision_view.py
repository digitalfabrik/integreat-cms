import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...constants import status
from ...decorators import permission_required
from ...models import Language

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_page"), name="dispatch")
class PageRevisionView(TemplateView):
    """
    View for browsing the page revisions and restoring old page revisions
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pages/page_revisions.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "pages"}

    def get(self, request, *args, **kwargs):
        r"""
        Render page revision slider

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = request.region
        page = get_object_or_404(region.pages, id=kwargs.get("page_id"))

        language = region.get_language_or_404(
            kwargs.get("language_slug"), only_active=True
        )

        page_translations = page.translations.filter(language=language)

        if not page_translations.exists():
            return redirect(
                "edit_page",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        if not request.user.has_perm("cms.change_page_object", page):
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
                    "language_slug": language.slug,
                },
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
                **self.get_context_data(**kwargs),
                "page": page,
                "page_translations": page_translations,
                "api_revision": page_translations.filter(status=status.PUBLIC).first(),
                "selected_revision": selected_revision.first(),
                "language": language,
            },
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        r"""
        Restore a previous revision of a page translation

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = request.region
        page = region.pages.get(id=kwargs.get("page_id"))

        language = Language.objects.get(slug=kwargs.get("language_slug"))

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
                    "language_slug": language.slug,
                },
            )

        if not request.user.has_perm("cms.change_page_object", page):
            raise PermissionDenied(
                f"{request.user!r} does not have the permission to restore {revision!r} of {page!r}"
            )

        current_revision = page.get_translation(language.slug)

        if (
            revision.slug == current_revision.slug
            and revision.title == current_revision.title
            and revision.content == current_revision.content
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
                    "language_slug": language.slug,
                },
            )

        revision.pk = None
        revision.version = current_revision.version + 1

        if "submit_draft" in request.POST:
            if not request.user.has_perm("cms.publish_page_object", page):
                raise PermissionDenied(
                    f"{request.user!r} does not have the permission to restore {revision!r} of {page!r} as draft"
                )
            revision.status = status.DRAFT
        elif "submit_review" in request.POST:
            revision.status = status.REVIEW
        elif "submit_public" in request.POST:
            if not request.user.has_perm("cms.publish_page_object", page):
                raise PermissionDenied(
                    f"{request.user!r} does not have the permission to restore the public {revision!r} of {page!r}"
                )
            revision.status = status.PUBLIC

        revision.save()

        messages.success(request, _("The revision was successfully restored"))

        page_translations = page.translations.filter(language=language)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "page": page,
                "page_translations": page_translations,
                "api_revision": page_translations.filter(status=status.PUBLIC).first(),
                "selected_revision": revision,
                "language": language,
            },
        )
