from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, OperationalError
from django.db.migrations.executor import MigrationExecutor


class Command(BaseCommand):
    help = 'Migrate, recovering a dropped connection only when no migrations remain.'

    def handle(self, *args, **options):
        for attempt in range(1, 4):
            try:
                call_command('migrate', interactive=False, stdout=self.stdout, stderr=self.stderr)
                return
            except OperationalError as exc:
                if attempt == 3 or not any(marker in str(exc).lower() for marker in (
                    'ssl syscall error: eof detected', 'server closed the connection unexpectedly',
                    'connection reset by peer',
                )):
                    raise
                connection = connections['default']
                connection.close()
                call_command('wait_for_db', timeout=90, interval=2,
                             stdout=self.stdout, stderr=self.stderr)
                executor = MigrationExecutor(connection)
                if executor.migration_plan(executor.loader.graph.leaf_nodes()):
                    raise CommandError(
                        'Database disconnected with unapplied migrations. '
                        'Inspect migration state before retrying deployment.'
                    ) from exc
                self.stdout.write(self.style.WARNING(
                    f'Database disconnected after migrations completed; '
                    f'retrying permission/content-type checks ({attempt}/2).'
                ))
