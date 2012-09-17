from django.core.management.base import BaseCommand

from django_bundles.conf.bundles_settings import bundles_settings
from django_bundles.core import get_bundles, set_bundle_versions
from django_bundles.processors import processor_pipeline, processor_library

import os
import shutil
from hashlib import md5
from tempfile import NamedTemporaryFile

def make_bundle(bundle):
    """
    Does all of the processing required to create a bundle and write it to disk, returning its hash version
    """
    hash_version = None

    with NamedTemporaryFile() as temp_output_file:
        for bundle_file in bundle.files:
            # Preprocess each file and copy onto temp_output_file
            bundle_file_output = processor_pipeline(bundle_file.processors, open(bundle_file.file_path, 'rb'))
            shutil.copyfileobj(bundle_file_output, temp_output_file)
            bundle_file_output.close()
            temp_output_file.write('\n')

        # Seek back to the start to run post processors
        temp_output_file.seek(0)

        # Post process the concatenated bundle
        processed_temp_output_file = processor_pipeline(bundle.processors, temp_output_file)
        processed_temp_output_file.seek(0)
        # Calculate a hash of the post processed file
        chunk_size = 2**14
        m = md5()
        while 1:
            chunk = processed_temp_output_file.read(chunk_size)
            if not chunk:
                break
            m.update(chunk)
        hash_version = m.hexdigest()

        processed_temp_output_file.seek(0)

        # Copy the file into its final location
        output_file_name = '%s.%s.%s' % (os.path.join(bundle.bundle_file_root, bundle.bundle_filename), hash_version, bundle.bundle_type)
        with open(output_file_name, 'wb') as output_file:
            shutil.copyfileobj(processed_temp_output_file, output_file)

        processed_temp_output_file.close()

    return hash_version

class Command(BaseCommand):
    help = "Bundles up the media"

    def handle(self, *args, **options):
        self.stdout.write("Bundling...\n")

        _bundle_versions = {}
        set_bundle_versions(_bundle_versions)

        for bundle in get_bundles():
            self.stdout.write("Writing bundle: %s\n" % bundle.name)

            hash_version = make_bundle(bundle)

            # Build bundle versions as we're going along in case they're used in templated bundles
            _bundle_versions[bundle.name] = hash_version
            self.stdout.write("\t%s\n" % bundle.get_version())

        version_info = '\n'.join(['    "%s": "%s",' % version for version in _bundle_versions.iteritems()])

        with open(bundles_settings.BUNDLES_VERSION_FILE, 'wb') as bundles_versions:
            bundles_versions.write("""\
#!/usr/bin/env python

BUNDLES_VERSIONS = {
%s
}
""" % version_info)

        for single_file_input, single_file_output in bundles_settings.BUNDLES_SINGLE_FILES:
            self.stdout.write("Writing: %s\n" % single_file_output)
            file_type = os.path.splitext(single_file_input)[1][1:]
            processors = processor_library.get_default_preprocessors_for(file_type) + processor_library.get_default_postprocessors_for(file_type)
            with processor_pipeline(processors, open(single_file_input, 'rb')) as temp_output:
                with open(single_file_output, 'wb') as output_file:
                    shutil.copyfileobj(temp_output, output_file)

        self.stdout.write("Done.\n")
