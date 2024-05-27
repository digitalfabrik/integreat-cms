"""
This file contains decorators that are used in core.
"""

import functools
from typing import Any, Callable


def disable_for_loaddata(function: Callable) -> Callable:
    """
    Mark a signal to not be run during the loaddata command

    :param function: The function that should not run during loaddata
    :return: The wrapped function
    """

    @functools.wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if kwargs.get("raw", False):
            return
        function(*args, **kwargs)

    return wrapper
