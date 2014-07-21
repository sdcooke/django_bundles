import os
import uuid

from optparse import make_option

from django.core.management.base import BaseCommand

from django_bundles.core import get_bundles
from django_bundles.processors import processor_pipeline
from django_bundles.utils.files import FileChunkGenerator


class Command(BaseCommand):
    args = "target_directory"
    help = "Writes out files containing the list of input files for each bundle"
    requires_model_validation = False
    option_list = BaseCommand.option_list + (
        make_option('--bundle-type',
            help='Limit output to specific bundle types',
        ),
    )

    def handle(self, target_directory, *args, **options):
        try:
            os.mkdir(target_directory)
        except OSError:
            pass

        for bundle in get_bundles():
            if options.get('bundle_type') and bundle.bundle_type != options.get('bundle_type'):
                continue
            manifest_filename = os.path.join(target_directory, bundle.name) + '.manifest'
            with open(manifest_filename, 'w') as manifest:
                for bundle_file in bundle.files:
                    if bundle_file.processors:
                        # The file has a preprocessor. This means in its current state it may not be a valid file
                        # and thus not suitable for inclusion in the manifest. Do any appropriate preprocessing and
                        # write out an appropriate version
                        output_pipeline = processor_pipeline(bundle_file.processors, FileChunkGenerator(open(bundle_file.file_path, 'rb')))
                        output_file_name = os.path.realpath(os.path.join(target_directory, '%s-%s.%s' % (str(uuid.uuid4())[-8:], os.path.split(bundle_file.file_path)[1], bundle.bundle_type)))
                        with open(output_file_name, 'wb') as output_file:
                            for chunk in output_pipeline:
                                output_file.write(chunk)
                        manifest.write(output_file_name + "\n")
                    else:
                        manifest.write(bundle_file.file_path + "\n")
