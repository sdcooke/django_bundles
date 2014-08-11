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
    help = "Watches the bundles to lint and preprocess files"
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

        self.log_lines = self.log_lines[-10:]
        self.drawscreen()

    def log_precompile_result(self, src):
        self.log_lines.append(self.style.HTTP_SUCCESS('PRECOMPILED\t\t%s' % src))
        self.log_lines = self.log_lines[-10:]
        self.drawscreen()


    def handle(self, *args, **options):
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

        def precompile(full_path, bundle):
            if bundle.precompile_in_debug and bundle[full_path].processors:
                with open(bundle[full_path].precompile_path, 'wb') as output_file:
                    for chunk in processor_pipeline(bundle[full_path].processors, FileChunkGenerator(open(full_path, 'rb'))):
                        output_file.write(chunk)
                self.log_precompile_result(full_path)

        def check_and_lint_file(src):
            full_path = os.path.realpath(os.path.join(os.getcwd(), src))

            for watchdir in watching:
                if watchdir in src:
                    for bundle in watching[watchdir]:
                        if full_path in bundle:
                            precompile(full_path, bundle)
                            result, error_message = self.lint_file(bundle.bundle_type, full_path, iter_input=processor_pipeline(bundle[full_path].processors, FileChunkGenerator(open(full_path, 'rb'))))
                            self.log_watch_result(full_path, result, error_message=error_message)
                            return

        class FileEventHandler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory:
                    check_and_lint_file(event.src_path)

            def on_modified(self, event):
                if not event.is_directory:
                    check_and_lint_file(event.src_path)

        event_handler = FileEventHandler()
        observer = Observer()
        curses.setupterm()
        self.drawscreen()

        initial_run = set()

        for bundle in get_bundles():
            watch_path = bundle.files_root.replace(os.getcwd(), '.')
            if watch_path not in watching:
                watching[watch_path] = set()
                observer.schedule(event_handler, path=watch_path, recursive=True)
            watching[watch_path].add(bundle)

            for bundle_file in bundle.files:
                if bundle_file in initial_run:
                    continue
                initial_run.add(bundle_file)
                precompile(bundle_file.file_path, bundle)

        observer.start()
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
