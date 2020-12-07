from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...models import Region, Language


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class POIListView(PermissionRequiredMixin, TemplateView):
    """
    View for listing POIs (points of interests)
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_pois"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: Template for list of non-archived POIs
    template = "pois/poi_list.html"
    #: Template for list of archived POIs
    template_archived = "pois/poi_list_archived.html"
    #: Whether or not to show archived POIs
    archived = False
    #: Messages in confirmation dialogs for delete, archive, restore operations
    confirmation_dialog_context = {
        "archive_dialog_title": ugettext_lazy(
            "Please confirm that you really want to archive this location"
        ),
        "archive_dialog_text": ugettext_lazy(
            "All translations of this location will also be archived."
        ),
        "restore_dialog_title": ugettext_lazy(
            "Please confirm that you really want to restore this location"
        ),
        "restore_dialog_text": ugettext_lazy(
            "All translations of this location will also be restored."
        ),
        "delete_dialog_title": ugettext_lazy(
            "Please confirm that you really want to delete this location"
        ),
        "delete_dialog_text": ugettext_lazy(
            "All translations of this location will also be deleted."
        ),
    }

    @property
    def template_name(self):
        """
        Select correct HTML template, depending on :attr:`~cms.views.pois.poi_list_view.POIListView.archived` flag
        (see :class:`~django.views.generic.base.TemplateResponseMixin`)

        :return: Path to HTML template
        :rtype: str
        """
        return self.template_archived if self.archived else self.template

    def get(self, request, *args, **kwargs):
        """
        Render POI list

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        # current region
        region_slug = kwargs.get("region_slug")
        region = Region.get_current_region(request)

        # current language
        language_code = kwargs.get("language_code")
        if language_code:
            language = Language.objects.get(code=language_code)
        elif region.default_language:
            return redirect(
                "pois",
                **{
                    "region_slug": region_slug,
                    "language_code": region.default_language.code,
                }
            )
        else:
            messages.error(
                request,
                _(
                    "Please create at least one language node before creating locations."
                ),
            )
            return redirect(
                "language_tree",
                **{
                    "region_slug": region_slug,
                }
            )

        if language != region.default_language:
            messages.warning(
                request,
                _(
                    "You can only create locations in the default language (%(language)s)."
                )
                % {"language": region.default_language.translated_name},
            )

        return render(
            request,
            self.template_name,
            {
                "current_menu_item": "pois",
                "pois": region.pois.filter(archived=self.archived),
                "archived_count": region.pois.filter(archived=True).count(),
                "language": language,
                "languages": region.languages,
                **self.confirmation_dialog_context,
            },
        )
