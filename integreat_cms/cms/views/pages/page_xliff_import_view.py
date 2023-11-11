from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ....xliff.utils import get_xliff_import_diff, xliff_import_confirm
from ...decorators import permission_required
from .page_context_mixin import PageContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse
    from django.http.response import HttpResponseRedirect

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_page"), name="dispatch")
class PageXliffImportView(TemplateView, PageContextMixin):
    """
    View for importing uploaded XLIFF files
    """

    #: Template for XLIFF import view
    template_name = "pages/page_xliff_import_view.html"

    # Custom attributes:
    #: The region of this view
    region = None
    #: The language of this view
    language = None
    #: The upload directory of this import
    xliff_dir = None

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :return: The template context
        """
        if TYPE_CHECKING:
            assert self.xliff_dir
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_menu_item": "pages",
                "upload_dir": os.path.basename(self.xliff_dir),
                "translation_diffs": get_xliff_import_diff(
                    self.request, self.xliff_dir
                ),
                "language": self.language,
            }
        )
        return context

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Redirect to page tree if XLIFF directory does not exist

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        # Get current region and language
        self.region = request.region
        if TYPE_CHECKING:
            assert self.region
        self.language = self.region.get_language_or_404(
            kwargs.get("language_slug"), only_active=True
        )
        # Get directory path of the uploaded XLIFF files
        self.xliff_dir = os.path.join(
            settings.XLIFF_UPLOAD_DIR, str(kwargs.get("xliff_dir"))
        )

        if not os.path.isdir(self.xliff_dir):
            messages.error(
                request,
                _("This XLIFF import is no longer available."),
            )
            return redirect(
                "pages",
                **{
                    "region_slug": self.region.slug,
                    "language_slug": self.language.slug,
                },
            )
        return super().dispatch(request, *args, **kwargs)

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        r"""
        Confirm the xliff import

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        if TYPE_CHECKING:
            assert self.region
            assert self.language
            assert self.xliff_dir
        logger.info(
            "XLIFF files of directory %r imported by %r",
            self.xliff_dir,
            request.user,
        )
        machine_translated = request.POST.get("machine_translated") == "on"
        if xliff_import_confirm(request, self.xliff_dir, machine_translated):
            return redirect(
                "pages",
                **{
                    "region_slug": self.region.slug,
                    "language_slug": self.language.slug,
                },
            )
        return self.render_to_response(self.get_context_data(**kwargs))
