from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...utils.media_utils import attach_file
from ...decorators import region_permission_required
from ...forms import DocumentForm
from ...models import Document, Region, Directory


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class MediaEditView(TemplateView):
    """
    View for editing media elements
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "media/media_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "media_upload"}

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.media.document_form.DocumentForm`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        slug = kwargs.get("region_slug")
        directory_id = kwargs.get("directory_id")
        region = Region.objects.get(slug=slug)
        document_id = kwargs.get("document_id")
        form = DocumentForm()
        if document_id != "0":
            document = Document.objects.get(id=document_id)
            form = DocumentForm(instance=document)

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "form": form,
                "region_slug": region.slug,
                "directory_id": directory_id,
                "document_id": document_id,
            },
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        """
        Submit :class:`~cms.forms.media.document_form.DocumentForm` and save both the
        :class:`~cms.models.media.document.Document` object in the database and file on the file system

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

        directory_id = int(kwargs.get("directory_id"))
        document_id = kwargs.get("document_id")
        directory = None
        if directory_id != 0:
            directory = Directory.objects.get(id=directory_id)

        form = DocumentForm()

        if "upload" in request.FILES:
            document = Document()
            document.region = region
            document.path = directory
            document.name = request.FILES["upload"].name
            attach_file(document, request.FILES["upload"])
            document.save()
            return redirect(
                "media", **{"region_slug": region.slug, "directory_id": directory_id}
            )

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "region_slug": region.slug,
                "directory_id": directory_id,
                "document_id": document_id,
            },
        )
