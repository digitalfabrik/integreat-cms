"""
Context processors pass additional variables to templates (see :ref:`context-processors`).
"""
from integreat_cms import __version__


# pylint: disable=unused-variable
def version_processor(request):
    """
    This context processor injects the current package version into the template context.

    :param request: The current http request
    :type request: ~django.http.HttpRequest

    :return: The currently installed version of this package
    :rtype: dict
    """
    return {"version": __version__}
