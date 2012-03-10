from django.core.management.base import BaseCommand

from django_bundles.core import get_bundles
from django_bundles.processors import processor_pipeline
from django_bundles.utils import run_command
from django_bundles.conf.bundles_settings import bundles_settings

class Command(BaseCommand):
    help = "Lints the bundles based on settings.BUNDLES_LINTING"

    def handle(self, *args, **options):
        failures = 0
        for bundle in get_bundles():
            for bundle_file in bundle.files:
                if bundle_file.lint:
                    with processor_pipeline(bundle_file.processors, open(bundle_file.file_path, 'rb'), require_actual_file=True) as file_output:
                        file_output.seek(0)

                        stdout, stderr = run_command(bundles_settings.BUNDLES_LINTING[bundle.bundle_type]['command'] % {
                            'infile': file_output.name
                        })

                        if stdout.strip() == 'OK':
                            self.stdout.write('OK\t\t%s\n' % bundle_file.file_path)
                        else:
                            failures += 1
                            self.stdout.write('FAIL\t\t%s\n' % bundle_file.file_path)
                            self.stdout.write(stdout)
        if failures:
            self.stdout.write('\n%s FILE%s FAILED\n' % (failures, 'S' if failures > 1 else ''))
        else:
            self.stdout.write('\nSUCCESS\n')