from typing import Any

from django.core.management.commands.loaddata import Command as LoaddataCommand
from django.dispatch import Signal

pre_loaddata = Signal()
post_loaddata = Signal()


class Command(LoaddataCommand):
    __doc__ = f"""
    Wrapper around djangos loaddata command to emit signals before and after loading data.
    This command acts as a drop-in replacement by shadowing the original one.

    {LoaddataCommand.__doc__}
    """

    def handle(self, *fixture_labels: Any, **options: Any) -> None:
        pre_loaddata.send(sender=self.__class__, fixture_labels=fixture_labels)

        super().handle(*fixture_labels, **options)

        post_loaddata.send(sender=self.__class__, fixture_labels=fixture_labels)


Command.handle.__doc__ = f"""
{LoaddataCommand.handle.__doc__}

Emits a signal before and after loading.
"""
