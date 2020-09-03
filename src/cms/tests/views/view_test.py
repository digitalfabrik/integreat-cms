from django.test import TestCase


class ViewTest(TestCase):
    """
    This test class is a helper class for other view tests.
    It does not contain tests on its own, but only helper functions for subclasses.
    """

    def assertHttp200(self, response):
        """
        This function checks whether the given response returns the http status code 200 and lets a test fail if not.

        :param response: The given http response
        :type response: django.http.HttpResponse
        """
        status_code = response.status_code
        self.assertEqual(
            status_code,
            200,
            "Expected a HTTP 200 response, but got HTTP %d" % status_code,
        )
