"""
Management command: seed_all_if_empty
Runs all learning seed commands only when the database has no modules.
Safe to include in the Procfile — skips silently on subsequent deploys.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from learning.models import LearningModule


class Command(BaseCommand):
    help = 'Seed all learning modules and quizzes if the database is empty'

    def handle(self, *args, **options):
        if LearningModule.objects.exists():
            self.stdout.write('Learning modules already exist — skipping seed.')
            return

        self.stdout.write('No modules found — seeding learning data...')
        call_command('seed_learning')
        call_command('seed_modules')
        call_command('seed_advanced_modules')
        call_command('seed_new_modules')
        call_command('seed_quizzes')
        call_command('seed_remaining_quizzes')
        call_command('seed_new_quizzes')
        self.stdout.write(self.style.SUCCESS('Seeding complete.'))
