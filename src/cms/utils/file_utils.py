"""
This module contains helpers for file handling.
"""

from ..forms import DocumentForm


def save_file(request):
    """
    This function accepts uploaded files, checks if they are valid in respect to the
    :class:`~cms.forms.media.document_form.DocumentForm` and stores them to disk if so.

    Example usage: :class:`cms.views.media.media_edit_view.MediaEditView`

    :param request: The current request submitting the file(s)
    :type request: ~django.http.HttpRequest

    :return: A dictionary containing the :class:`~cms.forms.media.document_form.DocumentForm` object and the boolean return status
    :rtype: dict
    """

    status = 0
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            status = 1
    else:
        form = DocumentForm()

    return {"form": form, "status": status}
