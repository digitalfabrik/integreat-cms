from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from ...constants import status
from ...decorators import permission_required
from ...models import Language


@method_decorator(permission_required("cms.view_event"), name="dispatch")
class EventRevisionView(TemplateView):
    """
    View for browsing the event revisions and restoring old event revisions
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "events/event_revisions.html"

    def get(self, request, *args, **kwargs):
        r"""
        Render event revision slider

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific event

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = request.region
        event = get_object_or_404(region.events, id=kwargs.get("event_id"))

        language = region.get_language_or_404(
            kwargs.get("language_slug"), only_active=True
        )

        event_translations = event.translations.filter(language=language)

        if not event_translations.exists():
            return redirect(
                "edit_event",
                **{
                    "event_id": event.id,
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        if not request.user.has_perm("cms.change_event_object", event):
            messages.warning(
                request,
                _("You don't have the permission to restore versions of this event."),
            )

        selected_revision = event_translations.filter(
            version=kwargs.get("selected_revision", event_translations.count())
        )

        if not selected_revision.exists():
            messages.error(request, _("This revision does not exist."))
            return redirect(
                "event_revisions",
                **{
                    "event_id": event.id,
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        if event.archived:
            messages.warning(
                request,
                _("You cannot restore versions of this event because it is archived."),
            )

        return render(
            request,
            self.template_name,
            {
                "api_revision": event_translations.filter(status=status.PUBLIC).first(),
                "event": event,
                "event_translations": event_translations,
                "language": language,
                "selected_revision": selected_revision,
            },
        )

    def post(self, request, *args, **kwargs):
        r"""
        Restore a previous revision of a event translation

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific event

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = request.region
        event = region.events.get(id=kwargs.get("event_id"))
        language = Language.objects.get(slug=kwargs.get("language_slug"))

        revision = event.translations.filter(
            language=language, version=request.POST.get("revision")
        ).first()

        redirect_to_event_revisions = redirect(
            "event_revisions",
            **{
                "event_id": event.id,
                "region_slug": region.slug,
                "language_slug": language.slug,
            },
        )

        if not revision:
            messages.error(request, _("This revision does not exist."))
            return redirect_to_event_revisions

        if not request.user.has_perm("cms.change_event_object", event):
            raise PermissionDenied(
                f"{request.user!r} does not have the permission to restore {revision!r} of {event!r}"
            )

        current_revision = event.get_translation(language.slug)

        if not (desired_status := request.POST.get("status")):
            # If the current version should be rejected, return to the latest version that is neither an auto save nor in review
            revision = event.translations.filter(
                language=language, status__in=[status.DRAFT, status.PUBLIC]
            ).first()
            if not revision:
                messages.error(
                    request,
                    _("You cannot reject changes if there is no version to return to."),
                )
                return redirect_to_event_revisions
            desired_status = revision.status
        elif desired_status not in dict(status.CHOICES):
            raise PermissionDenied(
                f"{request.user!r} tried to restore {revision!r} of {event!r} with invalid status {desired_status!r}"
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
                return redirect_to_event_revisions

        if desired_status == status.DRAFT and not request.user.has_perm(
            "cms.publish_event_object", event
        ):
            raise PermissionDenied(
                f"{request.user!r} does not have the permission to restore {revision!r} of {event!r} as draft"
            )

        if desired_status == status.PUBLIC and not request.user.has_perm(
            "cms.publish_event_object", event
        ):
            raise PermissionDenied(
                f"{request.user!r} does not have the permission to restore the public {revision!r} of {event!r}"
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

        return redirect_to_event_revisions
