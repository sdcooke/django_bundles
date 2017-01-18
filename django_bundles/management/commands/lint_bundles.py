from subprocess import CalledProcessError
from django.core.management.base import BaseCommand, CommandError

from django_bundles.core import get_bundles
from django_bundles.processors import processor_pipeline
from django_bundles.utils.files import FileChunkGenerator
from django_bundles.utils.processes import run_process
from django_bundles.conf.bundles_settings import bundles_settings

import collections

import os
from tempfile import NamedTemporaryFile
from multiprocessing.dummy import Pool


def lint_file(bundle_type, file_path, iter_input=None):
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


def do_lint_file(args):
    bundle_type, file_path, processors = args
    success, error_message = lint_file(bundle_type, file_path, iter_input=processor_pipeline(processors, FileChunkGenerator(open(file_path, 'rb'))))
    return success, error_message, file_path


class Command(BaseCommand):
    help = "Lints the bundles based on settings.BUNDLES_LINTING"
    requires_model_validation = False

    def add_arguments(self, parser):
        parser.add_argument('--failures-only', action='store_true', default=False, help='Only report failures')
        parser.add_argument('--pattern', help='Simple pattern matching for files')
        parser.add_argument('--parallel', action='store_true', default=False, help='Parallel for speed')

    def handle(self, *args, **options):
        show_successes = not bool(options['failures_only'])
        file_pattern = options['pattern']

        failures = 0
        files_added = set()
        files_to_lint = []

        for bundle in get_bundles():
            for bundle_file in bundle.files:
                if file_pattern and file_pattern not in bundle_file.file_path:
                    continue

                # Check the file exists, even for non-linted files
                if not os.path.exists(bundle_file.file_path):
                    self.stdout.write(self.style.HTTP_SERVER_ERROR('FAIL\t\t%s\n' % bundle_file.file_path))
                    self.stdout.write(self.style.HTTP_SERVER_ERROR('File does not exist (referenced from %s)\n' % bundle.name))
                    failures += 1
                    continue

                if not bundle_file.lint or bundle_file.file_path in files_added:
                    continue

                files_added.add(bundle_file.file_path)
                files_to_lint.append((
                    bundle.bundle_type,
                    bundle_file.file_path,
                    bundle_file.processors,
                ))

        def handle_result(success, error_message, file_path):
            if success:
                if show_successes:
                    self.stdout.write(self.style.HTTP_SUCCESS('OK\t\t%s\n' % file_path))
                return 0
            else:
                self.stdout.write(self.style.HTTP_SERVER_ERROR('FAIL\t\t%s\n' % file_path))
                self.stdout.write(self.style.HTTP_SERVER_ERROR(error_message))
                return 1

        if options['parallel']:
            pool = Pool()
            results = pool.map(do_lint_file, files_to_lint)
            pool.close()
            pool.join()

            for success, error_message, file_path in results:
                failures += handle_result(success, error_message, file_path)
        else:
            for bundle_type, file_path, processors in files_to_lint:
                success, error_message, _ = do_lint_file((bundle_type, file_path, processors))
                failures += handle_result(success, error_message, file_path)

        for single_file_path, _ in bundles_settings.BUNDLES_SINGLE_FILES:
            success, error_message = lint_file(os.path.splitext(single_file_path)[1][1:], single_file_path)
            failures += handle_result(success, error_message, single_file_path)

        if failures:
            raise CommandError('%s FILE%s FAILED' % (failures, 'S' if failures > 1 else ''))
        else:
            self.stdout.write(self.style.HTTP_REDIRECT('\nALL FILES PASSED\n'))
