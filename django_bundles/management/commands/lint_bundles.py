from django.core.management.base import BaseCommand

from django_bundles.core import get_bundles
from django_bundles.processors import processor_pipeline
from django_bundles.utils import run_command
from django_bundles.conf.bundles_settings import bundles_settings

import os


class Command(BaseCommand):
    help = "Lints the bundles based on settings.BUNDLES_LINTING"

    def lint_file(self, filename, bundle_type, bundle_path):
        stdout, stderr = run_command(bundles_settings.BUNDLES_LINTING[bundle_type]['command'] % {
            'infile': filename
        })

        if (bundles_settings.BUNDLES_LINT_SUCCESS_OK and stdout.strip() == 'OK') or (not bundles_settings.BUNDLES_LINT_SUCCESS_OK and not stdout.strip()):
            self.stdout.write('OK\t\t%s\n' % bundle_path)
            failures = 0
        else:
            failures = 1
            self.stdout.write('FAIL\t\t%s\n' % bundle_path)
            self.stdout.write(stdout)

        return failures

    def handle(self, *args, **options):
        failures = 0
        for bundle in get_bundles():
            for bundle_file in bundle.files:
                if bundle_file.lint:
                    with processor_pipeline(bundle_file.processors, open(bundle_file.file_path, 'rb'), require_actual_file=True) as file_output:
                        file_output.seek(0)
                        failures += self.lint_file(file_output.name, bundle.bundle_type, bundle_file.file_path)

        for single_file_path, _ in bundles_settings.BUNDLES_SINGLE_FILES:
            failures += self.lint_file(single_file_path, os.path.splitext(single_file_path)[1][1:], single_file_path)

        if failures:
            self.stdout.write('\n%s FILE%s FAILED\n' % (failures, 'S' if failures > 1 else ''))
        else:
            self.stdout.write('\nSUCCESS\n')
