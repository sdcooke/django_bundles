from django.core.management.base import BaseCommand

from django_bundles.conf.bundles_settings import bundles_settings
from django_bundles.core import get_bundles, set_bundle_versions
from django_bundles.processors import processor_pipeline, processor_library
from django_bundles.utils.files import FileChunkGenerator

import os
from hashlib import md5


def iter_bundle_files(bundle, debug=False):
    for bundle_file in bundle.files:
        for chunk in processor_pipeline(bundle_file.processors, FileChunkGenerator(open(bundle_file.file_path, 'rb')), debug=debug):
            yield chunk
        yield '\n'


def make_bundle(bundle, debug=False):
    """
    Does all of the processing required to create a bundle and write it to disk, returning its hash version
    """
    iter_input = iter_bundle_files(bundle, debug=debug)

    output_pipeline = processor_pipeline(bundle.processors, iter_input, debug=debug)

    m = md5()

    tmp_output_file_name = '%s.%s.%s' % (os.path.join(bundle.bundle_file_root, bundle.bundle_filename), 'temp', bundle.bundle_type)

    with open(tmp_output_file_name, 'wb') as output_file:
        for chunk in output_pipeline:
            m.update(chunk)
            output_file.write(chunk)

    hash_version = m.hexdigest()

    if debug:
        output_file_name = '%s.debug.%s.%s' % (os.path.join(bundle.bundle_file_root, bundle.bundle_filename), hash_version, bundle.bundle_type)
    else:
        output_file_name = '%s.%s.%s' % (os.path.join(bundle.bundle_file_root, bundle.bundle_filename), hash_version, bundle.bundle_type)

    os.rename(tmp_output_file_name, output_file_name)

    return hash_version


class Command(BaseCommand):
    help = "Bundles up the media"
    requires_model_validation = False

    def handle(self, *args, **options):
        self.stdout.write("Bundling...\n")

        _bundle_versions = {}
        set_bundle_versions(_bundle_versions)

        for bundle in get_bundles():
            self.stdout.write("Writing bundle: %s\n" % bundle.name)

            hash_version = make_bundle(bundle)

            # Build bundle versions as we're going along in case they're used in templated bundles
            _bundle_versions[bundle.name] = hash_version

            if bundle.create_debug:
                _bundle_versions['debug:' + bundle.name] = make_bundle(bundle, debug=True)

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

            with open(single_file_output, 'wb') as output_file:
                for chunk in processor_pipeline(processors, FileChunkGenerator(open(single_file_input, 'rb'))):
                    output_file.write(chunk)

        self.stdout.write("Done.\n")
