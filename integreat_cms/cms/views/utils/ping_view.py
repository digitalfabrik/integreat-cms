from django.http import HttpResponse
from django.views import View


class PingView(View):
    """
    Simple ping view
    """

    def get(self, request, *args, **kwargs):
        r"""
        Return dummy response

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: A dummy response
        :rtype: ~django.http.HttpResponse
        """
        return HttpResponse("pong")
