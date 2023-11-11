from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView

from ...forms import LinkReplaceForm

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse


class LinkReplaceView(TemplateView):
    """
    View for link replace form
    """

    template_name = "linkcheck/search_and_replace_link.html"

    extra_context = {
        "current_menu_item": "linkcheck",
    }

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render link replace form

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        form = LinkReplaceForm(
            region=self.request.region, initial={"link_types": ["internal"]}
        )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "form": form,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Applies link replace form

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.http.Http404: HTTP status 404 if the edited URL does not exist

        :return: Redirect to broken link list
        """
        form = LinkReplaceForm(data=request.POST, region=self.request.region)

        if not form.is_valid():
            for field in form:
                for error in field.errors:
                    messages.error(request, f"{_(field.label)}: {_(error)}")
            for error in form.non_field_errors():
                messages.error(request, _(error))
            return render(
                request,
                self.template_name,
                {
                    **self.get_context_data(**kwargs),
                    "form": form,
                },
            )

        form.save()

        messages.success(
            request,
            _("Links were replaced successfully."),
        )

        return redirect(
            "linkcheck_landing",
            **{
                "region_slug": request.region.slug,
            },
        )
