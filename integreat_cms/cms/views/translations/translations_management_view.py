from __future__ import annotations

import logging
from collections import Counter
from typing import TYPE_CHECKING

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...constants.status import CHOICES
from ...decorators import permission_required
from ...forms import TranslationsManagementForm
from ...models import Event, Page, POI

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.manage_translations"), name="dispatch")
class TranslationsManagementView(TemplateView):
    """
    View for showing the machine translations management options
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "translations/translations_management.html"

    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "translations_management"}

    # pylint: disable=unused-variable
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Extend context by word counts

        :param \**kwargs: The supplied keyword arguments
        :return: The context dictionary
        """

        region = self.request.region
        content_types = [Event, POI, Page]

        word_count: dict[str, Counter] = {}

        for content_type in content_types:
            content_name = content_type._meta.verbose_name_plural.title()
            word_count[content_name] = Counter()
            for status, name in CHOICES:
                word_count[content_name][status] = 0

            contents = (
                region.get_pages(prefetch_translations=True)
                if content_type == Page
                else content_type.objects.filter(
                    region=region, archived=False
                ).prefetch_translations()
            )
            for content in contents:
                if latest_version := content.get_translation(
                    region.default_language.slug
                ):
                    word_count[content_name][latest_version.status] += len(
                        latest_version.content.split()
                    )

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "word_count": word_count,
                "total_public_words": sum(c["PUBLIC"] for c in word_count.values()),
                "total_draft_words": sum(c["DRAFT"] for c in word_count.values()),
                "total_review_words": sum(c["REVIEW"] for c in word_count.values()),
                "total_autosave_words": sum(
                    c["AUTO_SAVE"] for c in word_count.values()
                ),
            }
        )
        return context

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render translations management interface

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        form = TranslationsManagementForm(instance=request.region)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "form": form,
            },
        )

    @transaction.atomic
    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        r"""
        Submit :class:`~integreat_cms.cms.forms.translations.translations_management_form.TranslationsManagementForm` objects.

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

        :return: The rendered template response
        """

        form = TranslationsManagementForm(
            data=request.POST,
            instance=request.region,
        )

        if not form.is_valid():
            # Add error messages
            form.add_error_messages(request)
            return render(
                request,
                self.template_name,
                {
                    **self.get_context_data(**kwargs),
                    "form": form,
                },
            )

        # Save the machine translation settings
        form.save()

        messages.success(
            request,
            _("Automatic translation settings were saved successfully."),
        )

        return redirect(
            "translations_management",
            **{
                "region_slug": request.region.slug,
            },
        )
