import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from ...constants import status
from ...decorators import permission_required
from ...models import Language, ImprintPage

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_imprintpage"), name="dispatch")
@method_decorator(permission_required("cms.change_imprintpage"), name="post")
class ImprintRevisionView(TemplateView):
    """
    View for browsing the imprint revisions and restoring old imprint revisions
    """

    template_name = "imprint/imprint_revisions.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "imprint"}

    def get(self, request, *args, **kwargs):
        r"""
        Render imprint page revision slider

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.http.Http404: If no imprint exists for the region

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = request.region
        imprint = region.imprint
        if not imprint:
            raise Http404("No imprint found for this region")

        language = region.get_language_or_404(
            kwargs.get("language_slug"), only_active=True
        )

        imprint_translations = imprint.translations.filter(language=language)

        if not imprint_translations.exists():
            return redirect(
                "edit_imprint",
                **{
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        selected_revision = imprint_translations.filter(
            version=kwargs.get("selected_revision", imprint_translations.count())
        )

        if not selected_revision.exists():
            messages.error(request, _("This revision does not exist."))
            return redirect(
                "imprint_revisions",
                **{
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        # Show warning if user has no permission to manage the imprint
        if not request.user.has_perm("cms.change_imprintpage"):
            messages.warning(
                request,
                _("You don't have the permission restore revisions of the imprint."),
            )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "imprint": imprint,
                "imprint_translations": imprint_translations,
                "api_revision": imprint_translations.filter(
                    status=status.PUBLIC
                ).first(),
                "selected_revision": selected_revision.first(),
                "language": language,
            },
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        r"""
        Restore a previous revision of an imprint page translation

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.http.Http404: If no imprint exists for the region

        :raises ~django.core.exceptions.PermissionDenied: If user tries to restore a page with an invalid status

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = request.region
        try:
            imprint = region.imprint
        except ImprintPage.DoesNotExist as e:
            raise Http404 from e

        language = Language.objects.get(slug=kwargs.get("language_slug"))

        revision = imprint.translations.filter(
            language=language, version=request.POST.get("revision")
        ).first()

        if not revision:
            messages.error(request, _("This revision does not exist."))
            return redirect(
                "imprint_revisions",
                **{
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        current_revision = imprint.get_translation(language.slug)

        if (
            revision.title == current_revision.title
            and revision.content == current_revision.content
        ):
            messages.error(
                request,
                _(
                    "This revision is identical to the current version of this translation."
                ),
            )
            return redirect(
                "imprint_revisions",
                **{
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        revision.pk = None
        revision.version = current_revision.version + 1
        # Reset author to current user
        revision.creator = request.user

        desired_status = request.POST.get("status")

        if desired_status not in dict(status.CHOICES):
            raise PermissionDenied(
                f"{request.user!r} tried to restore {revision!r} of {imprint!r} with invalid status {desired_status!r}"
            )

        revision.status = desired_status
        revision.save()

        messages.success(request, _("The revision was successfully restored"))

        imprint_translations = imprint.translations.filter(language=language)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "imprint": imprint,
                "imprint_translations": imprint_translations,
                "api_revision": imprint_translations.filter(
                    status=status.PUBLIC
                ).first(),
                "selected_revision": revision,
                "language": language,
            },
        )
