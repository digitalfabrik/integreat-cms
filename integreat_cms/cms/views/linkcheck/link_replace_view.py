from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView

from ...forms import LinkReplaceForm


class LinkReplaceView(TemplateView):
    """
    View for link replace form
    """

    template_name = "linkcheck/search_and_replace_link.html"

    extra_context = {
        "current_menu_item": "linkcheck",
    }

    def get(self, request, *args, **kwargs):
        r"""
        Render link replace form

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
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

    def post(self, request, *args, **kwargs):
        r"""
        Applies link replace form

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.http.Http404: HTTP status 404 if the edited URL does not exist

        :return: Redirect to broken link list
        :rtype: ~django.http.HttpResponseRedirect
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
