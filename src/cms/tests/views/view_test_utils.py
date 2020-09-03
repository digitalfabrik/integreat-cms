"""
This modules contains helper functions for automatically generating view tests.
"""
from django.urls import reverse


def generate_test_functions(class_variables, views, kwargs):
    """
    This function generates test functions for a list of views.

    :param class_variables: The class variable dict in which the functions should be inserted
    :type class_variables: dict

    :param views: The list of views for which the test functions should be generated
    :type views: list

    :param kwargs: The kwargs dict which is passed to all views
    :type kwargs: dict
    """
    for view in views:
        # pylint: disable=cell-var-from-loop
        url = reverse(view, args=(), kwargs=kwargs)

        def test_function(self):
            response = self.client.get(url)
            self.assertHttp200(response)

        test_function.__name__ = f"test_{view}"
        test_function.__doc__ = (
            f"Test if the view ``{view}`` returns the HTTP status code ``200``"
        )
        class_variables[f"test_{view}"] = test_function
