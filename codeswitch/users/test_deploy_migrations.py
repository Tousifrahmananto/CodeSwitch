from io import StringIO
from unittest import TestCase
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError, connection
from django.test import TransactionTestCase


class DeployMigrationTests(TestCase):
    def run_command(self, failures):
        def run(name, **kwargs):
            if name == 'migrate':
                result = next(failures)
                if result:
                    raise result

        return patch('users.management.commands.migrate_for_deploy.call_command', side_effect=run)

    def test_reconnects_after_eof_when_migrations_are_complete(self):
        with self.run_command(iter([OperationalError('SSL SYSCALL error: EOF detected'), None])) as run, \
             patch('users.management.commands.migrate_for_deploy.connections') as connections, \
             patch('users.management.commands.migrate_for_deploy.MigrationExecutor') as executor:
            executor.return_value.migration_plan.return_value = []
            call_command('migrate_for_deploy', stdout=StringIO())
        self.assertEqual([call.args[0] for call in run.call_args_list], ['migrate', 'wait_for_db', 'migrate'])
        connections['default'].close.assert_called_once()

    def test_does_not_replay_unfinished_migrations(self):
        with self.run_command(iter([OperationalError('SSL SYSCALL error: EOF detected')])) as run, \
             patch('users.management.commands.migrate_for_deploy.connections'), \
             patch('users.management.commands.migrate_for_deploy.MigrationExecutor') as executor:
            executor.return_value.migration_plan.return_value = [(Mock(), False)]
            with self.assertRaisesRegex(CommandError, 'unapplied migrations'):
                call_command('migrate_for_deploy', stdout=StringIO())
        self.assertEqual(sum(call.args[0] == 'migrate' for call in run.call_args_list), 1)

    def test_other_database_errors_fail_without_retry(self):
        with self.run_command(iter([OperationalError('permission denied for table auth_permission')])) as run:
            with self.assertRaises(OperationalError):
                call_command('migrate_for_deploy', stdout=StringIO())
        self.assertEqual(run.call_count, 1)

    def test_disconnect_retries_are_bounded(self):
        with self.run_command(iter([OperationalError('SSL SYSCALL error: EOF detected')] * 3)) as run, \
             patch('users.management.commands.migrate_for_deploy.connections'), \
             patch('users.management.commands.migrate_for_deploy.MigrationExecutor') as executor:
            executor.return_value.migration_plan.return_value = []
            with self.assertRaises(OperationalError):
                call_command('migrate_for_deploy', stdout=StringIO())
        self.assertEqual(sum(call.args[0] == 'migrate' for call in run.call_args_list), 3)


class DeployMigrationIntegrationTests(TransactionTestCase):
    def test_real_permission_check_recovers_from_one_disconnect(self):
        disconnected = False

        def drop_once(execute, sql, params, many, context):
            nonlocal disconnected
            if not disconnected and sql.lstrip().upper().startswith('SELECT') and 'auth_permission' in sql:
                disconnected = True
                raise OperationalError('SSL SYSCALL error: EOF detected')
            return execute(sql, params, many, context)

        output = StringIO()
        with connection.execute_wrapper(drop_once):
            call_command('migrate_for_deploy', stdout=output)
        self.assertTrue(disconnected)
        self.assertIn('retrying permission/content-type checks', output.getvalue())

    def test_completed_database_runs_normal_migration_checks(self):
        output = StringIO()
        call_command('migrate_for_deploy', stdout=output)
        self.assertIn('No migrations to apply.', output.getvalue())
