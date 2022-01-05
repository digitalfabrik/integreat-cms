from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseRedirect
from django.views.generic.base import RedirectView


@method_decorator(login_required, name="dispatch")
class DismissTutorial(RedirectView):
    """
    View to mark a tutorial dismissed for the current user.
    If it was marked dismissed it should not be shown again automatically.
    """

    def post(self, request, *args, **kwargs):
        r"""
        Marks a tutorial as dismissed if one is provided in tutorial_id and dismiss_tutorial is set.

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.http.HttpResponseRedirect
        """
        redirect_url = request.POST.get("redirect_url", "/")

        tutorial_id = request.POST.get("tutorial_id")
        if request.POST.get("dismiss_tutorial") and tutorial_id:
            if tutorial_id == "page_tree_tutorial_seen":
                request.user.page_tree_tutorial_seen = True
            request.user.save()

        return HttpResponseRedirect(redirect_url)
