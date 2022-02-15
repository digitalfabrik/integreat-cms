from django.http import JsonResponse
from django.views.generic.base import View


class DismissTutorial(View):
    """
    View to mark a tutorial dismissed for the current user.
    If it was marked dismissed it should not be shown again automatically.
    """

    #: The list of HTTP method names that this view will accept.
    #: Since this changes the database, we want to have the csrf protection of post views.
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        r"""
        Marks a tutorial as dismissed

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.http.HttpResponseRedirect
        """

        tutorial_slug = kwargs.get("slug")
        if tutorial_slug == "page-tree":
            request.user.page_tree_tutorial_seen = True
        else:
            return JsonResponse(
                {"error": f"Tutorial '{tutorial_slug}' not found."}, status=404
            )

        request.user.save()

        return JsonResponse({"success": f"Tutorial '{tutorial_slug}' was dismissed."})
