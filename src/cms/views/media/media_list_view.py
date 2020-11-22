from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...models import Document


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class MediaListView(TemplateView):
    """
    View for listing media elements
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "media/media_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "media"}

    def get(self, request, *args, **kwargs):
        """
        Render media list

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        documents = Document.objects.all()

        return render(
            request, self.template_name, {**self.base_context, "documents": documents}
        )
