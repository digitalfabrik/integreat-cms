"""
This module contains the base view for bulk actions
"""
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView
from django.views.generic.list import MultipleObjectMixin

from cacheops import invalidate_model
from ...deepl_api.utils import DeepLApi
from ...summ_ai_api.summ_ai_api_client import SummAiApiClient

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
        redirect_kwargs = {
            "region_slug": self.request.region.slug,
        }
        # If this bulk action is bound to a language url paramter, also pass this to the redirect url
        if "language_slug" in kwargs:
            redirect_kwargs["language_slug"] = kwargs["language_slug"]
        return reverse(f"{self.model._meta.model_name}s", kwargs=redirect_kwargs)

    def get_queryset(self):
        """
        Get the queryset of selected items for this bulk action

        :raises ~django.http.Http404: HTTP status 404 if no objects with the given ids exist

        :return: The QuerySet of the filtered links
        :rtype: ~django.db.models.query.QuerySet
        """
        # This workaround is necessary to enable the async tests for the SUMM.AI client
        logger.debug("request body: %s", self.request.body)
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
        :type request: ~django.http.HttpRequest

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


class BulkActionEasyGermanView(BulkActionView):
    """
    Bulk action for translating multiple objects to Easy German
    """

    #: the form of this bulk action
    form = None

    def post(self, request, *args, **kwargs):
        r"""
        Translate multiple objects automatically to Easy German

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The redirect
        :rtype: ~django.http.HttpResponseRedirect
        """
        if not settings.SUMM_AI_ENABLED or not request.region.summ_ai_enabled:
            if not settings.SUMM_AI_ENABLED:
                logger.warning("SUMM.AI globally disabled")
            if not request.region.summ_ai_enabled:
                logger.warning("SUMM.AI disabled in %r", request.region)
            messages.error(request, _("Translations to Easy German are disabled"))
            return super().post(request, *args, **kwargs)
        # Collect the corresponding objects
        logger.info(
            "%r started SUMM.AI translation for: %r", request.user, self.get_queryset()
        )
        api_client = SummAiApiClient(request, self.form)
        api_client.translate_queryset(self.get_queryset())
        # Let the base view handle the redirect
        return super().post(request, *args, **kwargs)


class BulkUpdateBooleanFieldView(BulkActionView):
    """
    Bulk action for toggling boolean fields of multiple objects at once
    """

    #: The value of the field (defaults to ``True``)
    value = True

    @property
    def field_name(self):
        """
        Called when the bulk action is performed and the ``field_name`` attribute was not overwritten

        :raises NotImplementedError: If the ``field_name`` attribute is not implemented in the subclass
        """
        raise NotImplementedError(
            "Subclasses of BulkUpdateBooleanFieldView must provide a 'field_name' attribute"
        )

    @property
    def action(self):
        """
        Called when the bulk action is performed and the ``action`` attribute was not overwritten

        :raises NotImplementedError: If the ``action`` attribute is not implemented in the subclass
        """
        raise NotImplementedError(
            "Subclasses of BulkUpdateBooleanFieldView must provide an 'action' attribute"
        )

    def post(self, request, *args, **kwargs):
        r"""
        Update the fields of the selected objects and redirect

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The redirect
        :rtype: ~django.http.HttpResponseRedirect
        """

        # Archive objects
        self.get_queryset().update(**{self.field_name: self.value})
        # Invalidate cache
        invalidate_model(self.model)
        logger.debug(
            "Updated %s=%s for %r by %r",
            self.field_name,
            self.value,
            self.get_queryset(),
            request.user,
        )
        messages.success(
            request,
            _("The selected {} were successfully {}").format(
                self.model._meta.verbose_name_plural, self.action
            ),
        )
        # Let the base view handle the redirect
        return super().post(request, *args, **kwargs)


# pylint: disable=too-many-ancestors
class BulkArchiveView(BulkUpdateBooleanFieldView):
    """
    Bulk action for restoring multiple objects at once
    """

    #: The name of the archived-field
    field_name = "archived"

    #: The name of the action
    action = _("archived")


# pylint: disable=too-many-ancestors
class BulkRestoreView(BulkArchiveView):
    """
    Bulk action for restoring multiple objects at once
    """

    #: The value of the field
    value = False

    #: The name of the action
    action = _("restored")
