"""
This modules contains helper functions for automatically generating view tests.
"""
import json
import re


def generate_test_functions(class_variables, endpoint_data):
    """
    This function generates test functions for a list of views.

    :param class_variables: The class variable dict in which the functions should be inserted
    :type class_variables: dict

    :param endpoint_data: The list of endpoints for which the test functions should be generated
    :type endpoint_data: list
    """
    for endpoint, wp_endpoint, expected_result in endpoint_data:
        endpoint_str = re.sub("[^a-zA-Z0-9]", "_", endpoint.strip("/"))

        def test_function(
            self,
            endpoint=endpoint,
            wp_endpoint=wp_endpoint,
            expected_result=expected_result,
        ):
            response = self.client.get(endpoint, format="json")
            self.assertEqual(response.status_code, 200)
            response_wp = self.client.get(wp_endpoint, format="json")
            self.assertEqual(response_wp.status_code, 200)
            with open(expected_result, encoding="utf-8") as f:
                regions = json.load(f)
                self.assertEqual(regions, response.json())
                self.assertEqual(regions, response_wp.json())

        test_function.__name__ = f"test_{endpoint_str}"
        test_function.__doc__ = f"Test if the view ``{endpoint_str}`` returns the HTTP status code ``200`` with correct data"
        class_variables[f"test_{endpoint_str}"] = test_function
