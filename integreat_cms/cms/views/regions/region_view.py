import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import staff_required, permission_required
from ...forms import RegionForm
from ...models import Region
from ..media.media_context_mixin import MediaContextMixin

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
@method_decorator(permission_required("cms.view_region"), name="dispatch")
@method_decorator(permission_required("cms.change_region"), name="post")
class RegionView(TemplateView, MediaContextMixin):
    """
    View for the region form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "regions/region_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "regions"}

    def get(self, request, *args, **kwargs):
        r"""
        Render :class:`~integreat_cms.cms.forms.regions.region_form.RegionForm`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region_instance = Region.objects.filter(slug=kwargs.get("region_slug")).first()
        context = self.get_context_data(**kwargs)
        form = RegionForm(instance=region_instance)

        return render(
            request, self.template_name, {**self.base_context, **context, "form": form}
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        r"""
        Render :class:`~integreat_cms.cms.forms.regions.region_form.RegionForm` and save :class:`~integreat_cms.cms.models.regions.region.Region`
        object

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region_instance = Region.objects.filter(slug=kwargs.get("region_slug")).first()
        context = self.get_context_data(**kwargs)

        form = RegionForm(
            data=request.POST, files=request.FILES, instance=region_instance
        )

        if not form.is_valid():
            # Add error messages
            form.add_error_messages(request)
        elif not form.has_changed():
            # Add "no changes" messages
            messages.info(request, _("No changes made"))
        else:
            # Save form
            form.save()
            # Add the success message and redirect to the edit page
            if not region_instance:
                messages.success(
                    request,
                    _('Region "{}" was successfully created').format(
                        form.instance.name
                    ),
                )
                return redirect(
                    "edit_region",
                    region_slug=form.instance.slug,
                )
            # Add the success message
            messages.success(
                request,
                _('Region "{}" was successfully saved').format(form.instance.name),
            )

        return render(
            request, self.template_name, {"form": form, **self.base_context, **context}
        )
