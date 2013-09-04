import os

from django.core.management.base import BaseCommand

from django_bundles.core import get_bundles


class Command(BaseCommand):
    args = "target_directory"
    help = "Writes out files containing the list of input files for each bundle"
    requires_model_validation = False

    def handle(self, target_directory, *args, **options):
        try:
            os.mkdir(target_directory)
        except OSError:
            pass

        for bundle in get_bundles():
            manifest_filename = os.path.join(target_directory, bundle.name) + '.manifest'
            with open(manifest_filename, 'w') as manifest:
                manifest.write("\n".join(f.file_path for f in bundle.files))
