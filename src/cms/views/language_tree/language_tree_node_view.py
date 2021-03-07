from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...forms import LanguageTreeNodeForm
from ...models import Region


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class LanguageTreeNodeView(PermissionRequiredMixin, TemplateView):
    """
    Class that handles viewing single language in the language tree.
    This view is available within regions.
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_language_tree"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "language_tree/language_tree_node_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "language_tree_form"}

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.language_tree.language_tree_node_form.LanguageTreeNodeForm`

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
        region = Region.get_current_region(request)
        # current language tree node
        language_tree_node = region.language_tree_nodes.filter(
            id=kwargs.get("language_tree_node_id")
        ).first()

        language_tree_node_form = LanguageTreeNodeForm(
            instance=language_tree_node, region=region
        )
        return render(
            request,
            self.template_name,
            {
                "language_tree_node_form": language_tree_node_form,
                **self.base_context,
            },
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        """
        Save and show form for editing a single language (HTTP POST) in the language tree

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
        region = Region.get_current_region(request)
        # current language tree node
        language_tree_node_instance = region.language_tree_nodes.filter(
            id=kwargs.get("language_tree_node_id")
        ).first()
        language_tree_node_form = LanguageTreeNodeForm(
            data=request.POST, instance=language_tree_node_instance, region=region
        )

        if not language_tree_node_form.is_valid():
            for field in language_tree_node_form:
                for error in field.errors:
                    messages.error(request, _(error))
            for error in language_tree_node_form.non_field_errors():
                messages.error(request, _(error))

        elif not language_tree_node_form.has_changed():
            messages.info(request, _("No changes detected"))

        else:
            language_tree_node = language_tree_node_form.save()
            if language_tree_node_instance:
                messages.success(
                    request, _("Language tree node was successfully saved")
                )
            else:
                messages.success(
                    request, _("Language tree node was successfully created")
                )
            return redirect(
                "edit_language_tree_node",
                **{
                    "language_tree_node_id": language_tree_node.id,
                    "region_slug": region.slug,
                }
            )
        return render(
            request,
            self.template_name,
            {"language_tree_node_form": language_tree_node_form, **self.base_context},
        )
