from io import StringIO

from django.core.management import call_command


def get_command_output(command, *args, **kwargs):
    r"""
    Call a management command and return its output

    :param command: The command that is being invoked
    :type command: str

    :param \*args: The supplied arguments
    :type \*args: list

    :param \**kwargs: The supplied kwargs
    :type \**kwargs: dict

    :return: The stdout and stderr IO streams
    :rtype: tuple [ str ]
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
