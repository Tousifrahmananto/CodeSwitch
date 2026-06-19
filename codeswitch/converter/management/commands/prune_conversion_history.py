from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from converter.models import ConversionHistory


class Command(BaseCommand):
    help = 'Delete conversion history older than the configured retention period.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=settings.CONVERSION_HISTORY_RETENTION_DAYS)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=max(1, options['days']))
        queryset = ConversionHistory.objects.filter(timestamp__lt=cutoff)
        count = queryset.count()
        if not options['dry_run']:
            queryset.delete()
        action = 'Would delete' if options['dry_run'] else 'Deleted'
        self.stdout.write(self.style.SUCCESS(f'{action} {count} conversion records.'))
