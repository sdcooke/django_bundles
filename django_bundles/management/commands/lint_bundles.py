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
        make_option('--watch',
            action='store_true',
            default=False,
            help='Watch files for changes'
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


    def drawscreen(self):
        import curses

        self.stdout.write(curses.tigetstr('clear'))
        self.stdout.write("Watching files for changes...")

        if self.errored_files:
            self.stdout.write(self.style.ERROR('%s file%s to fix' % (len(self.errored_files), 's' if len(self.errored_files) > 1 else '')))
        else:
            self.stdout.write(self.style.HTTP_REDIRECT('no files to fix'))

        self.stdout.write("\n")

        self.stdout.write(curses.tigetstr('cud1') * 2)

        for filename, error_message in self.errored_files.iteritems():
            self.stdout.write('\t' + self.style.HTTP_SERVER_ERROR(filename) + '\n')
            self.stdout.write(self.style.HTTP_SERVER_ERROR('\n'.join(['\t\t' + error_line for error_line in error_message.split('\n')])) + '\n\n')

        self.stdout.write(curses.tigetstr('cud1') * 2)

        for log_line in reversed(self.log_lines):
            self.stdout.write('\t' + log_line + '\n')


    def log_watch_result(self, src, result, error_message=None):
        if result:
            if src in self.errored_files:
                del self.errored_files[src]
            self.log_lines.append(self.style.HTTP_SUCCESS('OK\t\t%s' % src))
        else:
            self.log_lines.append(self.style.HTTP_SERVER_ERROR('FAIL\t\t%s' % src))
            self.errored_files[src] = self.style.HTTP_SERVER_ERROR(error_message)

        self.log_lines = self.log_lines[-5:]
        self.drawscreen()


    def handle(self, *args, **options):
        self.show_successes = not bool(options.get('failures_only'))
        watch = bool(options.get('watch'))
        file_pattern = options.get('pattern')


        if watch:
            try:
                import time
                from watchdog.observers import Observer
                from watchdog.events import FileSystemEventHandler
                import curses
            except ImportError:
                raise CommandError('watchdog is required for this (pip install watchdog')

            self.errored_files = {}
            self.log_lines = []
            watching = {}

            def check_and_lint_file(src):
                # TODO: don't repeatedly lint the same file
                for watchdir in watching:
                    if watchdir in src:
                        for bundle in watching[watchdir]:
                            if src in bundle:
                                result, error_message = self.lint_file(bundle.bundle_type, src, iter_input=processor_pipeline(bundle[src].processors, FileChunkGenerator(open(src, 'rb'))))
                                self.log_watch_result(src, result, error_message=error_message)
                                break

            class FileEventHandler(FileSystemEventHandler):
                def on_created(self, event):
                    if not event.is_directory:
                        check_and_lint_file(event.src_path)

                def on_modified(self, event):
                    if not event.is_directory:
                        check_and_lint_file(event.src_path)

            # TODO: watchdog dirsnapshot line 97 patched (otherwise it doesn't work with PyCharm)
            #        #if stat_info.st_ino == ref_stat_info.st_ino and stat_info.st_mtime != ref_stat_info.st_mtime:
            #        if stat_info.st_mtime != ref_stat_info.st_mtime:

            event_handler = FileEventHandler()
            observer = Observer()
            curses.setupterm()
            self.drawscreen()

            for bundle in get_bundles():
                if bundle.files_root not in watching:
                    watching[bundle.files_root] = set()
                    observer.schedule(event_handler, path=bundle.files_root, recursive=True)
                watching[bundle.files_root].add(bundle)

            observer.start()
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()

            return


        files_linted = set()

        failures = 0

        def file_checked(success, error_message, file_path):
            if success:
                if self.show_successes:
                    self.stdout.write(self.style.HTTP_SUCCESS('OK\t\t%s\n' % file_path))
            else:
                failures += 1
                self.stdout.write(self.style.HTTP_SERVER_ERROR('FAIL\t\t%s\n' % file_path))
                self.stdout.write(self.style.HTTP_SERVER_ERROR(error_message))

            files_linted.add(file_path)

        for bundle in get_bundles():
            for bundle_file in bundle.files:
                if file_pattern and file_pattern not in bundle_file.file_path:
                    continue
                if not bundle_file.lint:
                    continue
                if bundle_file.file_path in files_linted:
                    continue

                success, error_message = self.lint_file(bundle.bundle_type, bundle_file.file_path, iter_input=processor_pipeline(bundle_file.processors, FileChunkGenerator(open(bundle_file.file_path, 'rb'))))

                file_checked(success, error_message, bundle_file.file_path)


        for single_file_path, _ in bundles_settings.BUNDLES_SINGLE_FILES:
            success, error_message = self.lint_file(os.path.splitext(single_file_path)[1][1:], single_file_path)
            file_checked(success, error_message, single_file_path)


        if failures:
            raise CommandError('%s FILE%s FAILED' % (failures, 'S' if failures > 1 else ''))
        else:
            self.stdout.write(self.style.HTTP_REDIRECT('\nALL FILES PASSED\n'))
