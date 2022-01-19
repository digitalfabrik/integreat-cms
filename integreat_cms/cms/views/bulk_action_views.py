"""
This module contains the base view for bulk actions
"""
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import RedirectView
from django.views.generic.list import MultipleObjectMixin

from cacheops import invalidate_model
from ...deepl_api.utils import DeepLApi

logger = logging.getLogger(__name__)


class BulkActionView(PermissionRequiredMixin, MultipleObjectMixin, RedirectView):
    """
    View for executing a bulk action and redirect to a given location
    """

    #: The list of HTTP method names that this view will accept.
    #: The bulk action form uses only POST as submission method.
    http_method_names = ["post"]
    #: Whether the view requires change permissions
    require_change_permission = True
    #: Whether the translation objects should be prefetched
    prefetch_translations = False
    #: Whether the public translation objects should be prefetched
    prefetch_public_translations = False

    def get_permission_required(self):
        """
        Override this method to override the permission_required attribute.

        :return: The permissions that are required for views inheriting from this Mixin
        :rtype: ~collections.abc.Iterable
        """
        # If the bulk action performs changes to the database, require the change permission
        if self.require_change_permission:
            return (f"cms.change_{self.model._meta.model_name}",)
        # If the bulk action is just a read-view (e.g. export), require the view permission
        return (f"cms.view_{self.model._meta.model_name}",)

    def get_redirect_url(self, *args, **kwargs):
        r"""
        Retrieve url for redirection

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: url to redirect to
        :rtype: str
        """
        return reverse(
            f"{self.model._meta.model_name}s",
            kwargs={
                "region_slug": self.request.region.slug,
                "language_slug": kwargs.get("language_slug"),
            },
        )

    def get_queryset(self):
        """
        Get the queryset of selected items for this bulk action

        :raises ~django.http.Http404: HTTP status 404 if no objects with the given ids exist

        :return: The QuerySet of the filtered links
        :rtype: ~django.db.models.query.QuerySet
        """
        queryset = (
            super()
            .get_queryset()
            .filter(
                region=self.request.region,
                id__in=self.request.POST.getlist("selected_ids[]"),
            )
        )
        if not queryset:
            raise Http404(f"No {self.model._meta.object_name} matches the given query.")
        if self.prefetch_translations:
            queryset = queryset.prefetch_translations()
        if self.prefetch_public_translations:
            queryset = queryset.prefetch_public_translations()
        return queryset


class BulkAutoTranslateView(BulkActionView):
    """
    Bulk action for automatically translating multiple objects
    """

    #: Whether the public translation objects should be prefetched
    prefetch_translations = True

    #: the form of this bulk action
    form = None

    def post(self, request, *args, **kwargs):
        r"""
        Translate multiple objects automatically

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The redirect
        :rtype: ~django.http.HttpResponseRedirect
        """
        if not settings.DEEPL_ENABLED:
            messages.error(request, _("Automatic translations are disabled"))
            return super().post(request, *args, **kwargs)
        # Collect the corresponding objects
        logger.debug("Automatic translation for: %r", self.get_queryset())
        deepl = DeepLApi()
        if deepl.check_availability(request, kwargs.get("language_slug")):
            deepl.deepl_translation(
                request, self.get_queryset(), kwargs.get("language_slug"), self.form
            )
        else:
            messages.warning(
                request,
                _(
                    "This language is not supported by DeepL. Please try another language"
                ),
            )

        # Let the base view handle the redirect
        return super().post(request, *args, **kwargs)


class BulkArchiveView(BulkActionView):
    """
    Bulk action for archiving multiple objects at once
    """

    #: The name of the archived-field
    archived_field = "archived"

    def post(self, request, *args, **kwargs):
        r"""
        Archive the selected objects and redirect

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The redirect
        :rtype: ~django.http.HttpResponseRedirect
        """

        # Archive objects
        self.get_queryset().update(**{self.archived_field: True})
        # Invalidate cache
        invalidate_model(self.model)
        logger.debug("%r archived by %r", self.get_queryset(), request.user)
        messages.success(
            request,
            _("The selected {} were successfully archived").format(
                self.model._meta.verbose_name_plural
            ),
        )
        # Let the base view handle the redirect
        return super().post(request, *args, **kwargs)


class BulkRestoreView(BulkActionView):
    """
    Bulk action for restoring multiple objects at once
    """

    #: The name of the archived-field
    archived_field = "archived"

    def post(self, request, *args, **kwargs):
        r"""
        Restore the selected objects and redirect

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The redirect
        :rtype: ~django.http.HttpResponseRedirect
        """
        # Restore objects
        self.get_queryset().update(**{self.archived_field: False})
        # Invalidate cache
        invalidate_model(self.model)
        logger.debug("%r restored by %r", self.get_queryset(), request.user)
        messages.success(
            request,
            _("The selected {} were successfully restored").format(
                self.model._meta.verbose_name_plural
            ),
        )
        # Let the base view handle the redirect
        return super().post(request, *args, **kwargs)
