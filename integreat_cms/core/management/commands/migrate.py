from typing import Any

from django.core.management.commands.migrate import Command as MigrateCommand
from django.dispatch import Signal

pre_full_migration = Signal()
post_full_migration = Signal()


class Command(MigrateCommand):
    __doc__ = f"""
    Wrapper around djangos migrate command to emit signals when a migration starts or ends.
    There exist the ``pre_migrate`` and ``post_migrate`` signals,
    but the latter are emitted multiple times during migration without any way to tell when the process has actually concluded.
    This command acts as a drop-in replacement by shadowing the original one.

    {MigrateCommand.__doc__}
    """

    def handle(self, *fixture_labels: Any, **options: Any) -> None:
        pre_full_migration.send(sender=self.__class__, fixture_labels=fixture_labels)

        super().handle(*fixture_labels, **options)

        post_full_migration.send(sender=self.__class__, fixture_labels=fixture_labels)


Command.handle.__doc__ = f"""
{MigrateCommand.handle.__doc__}

Emits a signal before and after migration.
"""
