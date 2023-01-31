"""
This file contains helper functions for tests.
"""
from lxml.etree import HTML, LxmlError, tostring


def assert_message_in_response(message, response):
    """
    Check whether a given message is in the messages div

    :param message: The expected message
    :type message: str

    :param response: The HTML content of the page
    :type response: str

    :raises AssertionError: When the response does not contain parsable HTML code
    """
    content = response.content.decode("utf-8")
    # Try to limit the output to the relevant messages
    try:
        root = HTML(content)
    except LxmlError as e:
        print(content)
        raise AssertionError("The response is invalid HTML") from e
    messages = root.xpath("//div[@id = 'messages']")
    assert (
        messages
    ), f'The div with id "messages" is missing in the response:\n\n{content}'
    content = tostring(messages[0], pretty_print=True, encoding="unicode")
    # Strip empty new lines for readability
    content = "".join([s for s in content.strip().splitlines(True) if s.strip()])
    assert (
        message in content
    ), f"Message '{message}' is missing in response:\n\n{content}"
