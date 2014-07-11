import os

from django.core.management.base import BaseCommand

from django_bundles.core import get_bundles
from django_bundles.processors import processor_pipeline
from django_bundles.utils.files import FileChunkGenerator


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
                for bundle_file in bundle.files:
                    if bundle_file.processors:
                        # The file has a preprocessor. This means in its current state it may not be a valid file
                        # and thus not suitable for inclusion in the manifest. Do any appropriate preprocessing and
                        # write out an appropriate version
                        output_pipeline = processor_pipeline(bundle_file.processors, FileChunkGenerator(open(bundle_file.file_path, 'rb')))
                        tmp_output_file_name = '%s.%s.%s' % (bundle_file.file_path, 'temp', bundle.bundle_type)
                        with open(tmp_output_file_name, 'wb') as output_file:
                            for chunk in output_pipeline:
                                output_file.write(chunk)
                        output_file_name = '%s.%s.%s' % (bundle_file.file_path, 'manifest', bundle.bundle_type)
                        os.rename(tmp_output_file_name, output_file_name)
                        manifest.write(output_file_name + "\n")
                    else:
                        manifest.write(bundle_file.file_path + "\n")
