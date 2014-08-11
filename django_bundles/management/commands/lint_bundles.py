from subprocess import CalledProcessError
from django.core.management.base import BaseCommand, CommandError

from django_bundles.core import get_bundles
from django_bundles.processors import processor_pipeline
from django_bundles.utils.files import FileChunkGenerator
from django_bundles.utils.processes import run_process
from django_bundles.conf.bundles_settings import bundles_settings

from optparse import make_option
import collections

import os
from tempfile import NamedTemporaryFile


class Command(BaseCommand):
    help = "Lints the bundles based on settings.BUNDLES_LINTING"
    option_list = BaseCommand.option_list + (
        make_option('--failures-only',
            action='store_true',
            default=False,
            help='Only report failures'
        ),
        make_option('--pattern',
            help='Simple pattern matching for files',
        ),
    )
    requires_model_validation = False

    def lint_file(self, bundle_type, file_path, iter_input=None):
        command = bundles_settings.BUNDLES_LINTING[bundle_type]['command']

        input_file = None
        stdin = None

        if '{infile}' in command:
            if iter_input:
                if hasattr(iter_input, 'file_path'):
                    filename = iter_input.file_path
                else:
                    input_file = NamedTemporaryFile()
                    for chunk in iter_input:
                        input_file.write(chunk)
                    input_file.flush()

                    filename = input_file.name
            else:
                filename = file_path

            command = command.format(infile=filename)
        else:
            if iter_input:
                stdin = iter_input
            else:
                stdin = input_file = open(file_path, 'rb')

        try:
            # Consume the iterator into a zero length deque
            collections.deque(run_process(command, stdin=stdin, to_close=input_file), maxlen=0)
        except CalledProcessError as e:
            return False, e.output

        return True, ''


    def handle(self, *args, **options):
        self.show_successes = not bool(options.get('failures_only'))
        watch = bool(options.get('watch'))
        file_pattern = options.get('pattern')

        files_linted = set()

        failures = 0

        def file_checked(success, error_message, file_path):
            files_linted.add(file_path)

            if success:
                if self.show_successes:
                    self.stdout.write(self.style.HTTP_SUCCESS('OK\t\t%s\n' % file_path))
                return 0
            else:
                self.stdout.write(self.style.HTTP_SERVER_ERROR('FAIL\t\t%s\n' % file_path))
                self.stdout.write(self.style.HTTP_SERVER_ERROR(error_message))
                return 1


        for bundle in get_bundles():
            for bundle_file in bundle.files:
                if file_pattern and file_pattern not in bundle_file.file_path:
                    continue
                if bundle_file.file_path in files_linted:
                    continue

                # Check the file exists, even for non-linted files
                if not os.path.exists(bundle_file.file_path):
                    self.stdout.write(self.style.HTTP_SERVER_ERROR('FAIL\t\t%s\n' % bundle_file.file_path))
                    self.stdout.write(self.style.HTTP_SERVER_ERROR('File does not exist (referenced from %s)\n' % bundle.name))
                    failures += 1
                    continue

                if not bundle_file.lint:
                    continue

                success, error_message = self.lint_file(bundle.bundle_type, bundle_file.file_path, iter_input=processor_pipeline(bundle_file.processors, FileChunkGenerator(open(bundle_file.file_path, 'rb'))))

                failures += file_checked(success, error_message, bundle_file.file_path)


        for single_file_path, _ in bundles_settings.BUNDLES_SINGLE_FILES:
            success, error_message = self.lint_file(os.path.splitext(single_file_path)[1][1:], single_file_path)
            failures += file_checked(success, error_message, single_file_path)


        if failures:
            raise CommandError('%s FILE%s FAILED' % (failures, 'S' if failures > 1 else ''))
        else:
            self.stdout.write(self.style.HTTP_REDIRECT('\nALL FILES PASSED\n'))
