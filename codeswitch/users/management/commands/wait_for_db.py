import time

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Wait until the configured database accepts connections.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=float,
            default=90,
            help='Maximum number of seconds to wait (default: 90).',
        )
        parser.add_argument(
            '--interval',
            type=float,
            default=2,
            help='Seconds between connection attempts (default: 2).',
        )

    def handle(self, *args, **options):
        timeout = max(options['timeout'], 0)
        interval = max(options['interval'], 0.1)
        deadline = time.monotonic() + timeout
        attempt = 0

        while True:
            attempt += 1
            try:
                # Discard a failed/stale connection before each retry.
                connection.close()
                connection.ensure_connection()
            except OperationalError as exc:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CommandError(
                        f'Database did not become ready within {timeout:g} seconds. '
                        f'Last connection error: {exc}'
                    ) from exc

                wait_seconds = min(interval, remaining)
                self.stdout.write(
                    self.style.WARNING(
                        f'Database is unavailable (attempt {attempt}); '
                        f'retrying in {wait_seconds:.1f}s...'
                    )
                )
                time.sleep(wait_seconds)
                continue

            self.stdout.write(
                self.style.SUCCESS(f'Database is ready after {attempt} attempt(s).')
            )
            return
