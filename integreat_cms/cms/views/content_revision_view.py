import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from ..constants import status
from ..decorators import permission_required
from ..models import Language, Page, POI
from .pages.page_context_mixin import PageContextMixin
from .pois.poi_context_mixin import POIContextMixin

logger = logging.getLogger(__name__)


class ContentRevisionView(TemplateView):
    """
    View for browsing the page/poi revisions and restoring old page/poi revisions
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "content_revisions.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)

    def get_context(self, request, *args, **kwargs):
        """
        Returns the context of current content

        To be implemented in the inheriting class
        """
        raise NotImplementedError

    def can_change_content(self, request, content):
        """
        Returns whether the user has permission to change the current content

        To be implemented in the inheriting class
        """
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        r"""
        Render page revision slider

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

        :raises ~django.http.Http404: HTTP status 404 if the content is not found

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        content_type = None
        content_name = ""

        if kwargs.get("page_id"):
            content_type = Page
            content_name = "page"
        elif kwargs.get("poi_id"):
            content_type = POI
            content_name = "poi"

        region = request.region
        content = (
            content_type.objects.filter(region=region)
            .filter(id=kwargs.get(f"{content_name}_id"))
            .first()
        )
        if not content:
            raise Http404("No Page matches the given region or id.")

        language = region.get_language_or_404(
            kwargs.get("language_slug"), only_active=True
        )
        content_translations = content.translations.filter(language=language)

        if not content_translations.exists():
            return redirect(
                f"edit_{content_name}",
                **{
                    f"{content_name}_id": content.id,
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        if not self.can_change_content(request, content):
            messages.warning(
                request,
                _("You don't have the permission to restore versions of this page."),
            )

        selected_revision = content_translations.filter(
            version=kwargs.get("selected_revision", content_translations.count())
        )

        if not selected_revision.exists():
            messages.error(request, _("This revision does not exist."))
            return redirect(
                f"{content_name}_revisions",
                **{
                    f"{content_name}_id": content.id,
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        if content.archived:
            messages.warning(
                request,
                _("You cannot restore versions of this page because it is archived."),
            )

        kwargs = {
            "region_slug": region.slug,
            "language_slug": language.slug,
            f"{content_name}_id": content.id,
        }
        revision = reverse(f"{content_name}_revisions", kwargs=kwargs)
        form = reverse(f"edit_{content_name}", kwargs=kwargs)

        return render(
            request,
            self.template_name,
            {
                **self.get_context(request, *args, **kwargs),
                "content_name": content_name,
                "content": content,
                "content_translations": content_translations,
                "api_revision": content_translations.filter(
                    status=status.PUBLIC
                ).first(),
                "selected_revision": selected_revision.first(),
                "language": language,
                "form": form,
                "revision": revision,
            },
        )

    # pylint: disable=too-many-branches
    def post(self, request, *args, **kwargs):
        r"""
        Restore a previous revision of a page translation

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        content_type = None
        content_name = ""

        if kwargs.get("page_id"):
            content_type = Page
            content_name = "page"
        elif kwargs.get("poi_id"):
            content_type = POI
            content_name = "poi"

        region = request.region
        content = (
            content_type.objects.filter(region=region)
            .filter(id=kwargs.get(f"{content_name}_id"))
            .first()
        )
        language = Language.objects.get(slug=kwargs.get("language_slug"))

        revision = content.translations.filter(
            language=language, version=request.POST.get("revision")
        ).first()

        redirect_to_content_revisions = redirect(
            f"{content_name}_revisions",
            **{
                f"{content_name}_id": content.id,
                "region_slug": region.slug,
                "language_slug": language.slug,
            },
        )

        if not revision:
            messages.error(request, _("This revision does not exist."))
            return redirect_to_content_revisions

        if not self.can_change_content(request, content):
            raise PermissionDenied(
                f"{request.user!r} does not have the permission to restore {revision!r} of {content!r}"
            )

        current_revision = content.get_translation(language.slug)

        if not (desired_status := request.POST.get("status")):
            # If the current version should be rejected, return to the latest version that is neither an auto save nor in review
            revision = content.translations.filter(
                language=language, status__in=[status.DRAFT, status.PUBLIC]
            ).first()
            if not revision:
                messages.error(
                    request,
                    _("You cannot reject changes if there is no version to return to."),
                )
                return redirect_to_content_revisions
            desired_status = revision.status
        elif desired_status not in dict(status.CHOICES):
            raise PermissionDenied(
                f"{request.user!r} tried to restore {revision!r} of {content!r} with invalid status {desired_status!r}"
            )

        # Assume that changing to an older revision is not a minor change by default
        minor_edit = False
        if (
            revision.slug == current_revision.slug
            and revision.title == current_revision.title
            and revision.content == current_revision.content
        ):
            minor_edit = True
            if desired_status == status.PUBLIC:
                if current_revision.status == status.PUBLIC:
                    messages.info(request, _("No changes detected, but date refreshed"))
                else:
                    messages.success(
                        request,
                        _("No changes detected, but status changed to published"),
                    )
            else:
                messages.error(
                    request,
                    _(
                        "This version is identical to the current version of this translation."
                    ),
                )
                return redirect_to_content_revisions

        if desired_status == status.DRAFT and not request.user.has_perm(
            "cms.publish_page_object", content
        ):
            raise PermissionDenied(
                f"{request.user!r} does not have the permission to restore {revision!r} of {content!r} as draft"
            )
        if desired_status == status.PUBLIC and not request.user.has_perm(
            "cms.publish_page_object", content
        ):
            raise PermissionDenied(
                f"{request.user!r} does not have the permission to restore the public {revision!r} of {content!r}"
            )

        # Delete all now outdated links
        current_revision.links.all().delete()
        # Create new version
        revision.pk = None
        revision.version = current_revision.version + 1
        revision.status = desired_status
        revision.minor_edit = minor_edit
        # Reset author to current user
        revision.creator = request.user
        revision.save()

        messages.success(request, _("The version was successfully restored"))

        return redirect_to_content_revisions


@method_decorator(permission_required("cms.view_page"), name="dispatch")
class PageRevisionView(ContentRevisionView, PageContextMixin):
    """
    View for browsing the page revisions and restoring old page revisions
    """

    def get_context(self, request, *args, **kwargs):
        r"""
        Get the context

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The template context
        :rtype: dict
        """
        return self.get_context_data(**kwargs)

    def can_change_content(self, request, content):
        r"""
        Check permission

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param content: the current page
        :type content: ~integreat_cms.cms.models.pages.page.Page

        :return: whether the user has permission to change the page
        :rtype: bool
        """
        return request.user.has_perm("cms.change_page_object", content)


@method_decorator(permission_required("cms.view_poi"), name="dispatch")
class POIRevisionView(ContentRevisionView, POIContextMixin):
    """
    View for browsing the poi revisions and restoring old poi revisions
    """

    def get_context(self, request, *args, **kwargs):
        r"""
        Get the context

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The template context
        :rtype: dict
        """
        return self.get_context_data(**kwargs)

    def can_change_content(self, request, content):
        r"""
        Check permission

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param content: the current poi
        :type content: ~integreat_cms.cms.models.pois.poi.POI

        :return: whether the user has permission cms.change_poi
        :rtype: bool
        """
        return request.user.has_perm("cms.change_poi")
