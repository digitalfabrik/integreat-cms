from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


from django.core.management import call_command


def get_command_output(command: str, *args: str, **kwargs: Any) -> tuple[str, str]:
    r"""
    Call a management command and return its output

    :param command: The command that is being invoked
    :param \*args: The supplied arguments
    :param \**kwargs: The supplied kwargs
    :return: The stdout and stderr IO streams
    """
    out = StringIO()
    err = StringIO()
    call_command(
        command,
        *args,
        stdout=out,
        stderr=err,
        **kwargs,
    )
    return out.getvalue(), err.getvalue()
