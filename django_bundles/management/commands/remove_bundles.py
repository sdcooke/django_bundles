import os
from django.core.management.base import BaseCommand

from django_bundles.conf.bundles_settings import bundles_settings
from django_bundles.core import get_bundles, get_bundle_versions

class Command(BaseCommand):
    help = "Removes any created bundles"
    requires_model_validation = False

    def handle(self, *args, **options):

        bundle_versions = get_bundle_versions()

        for bundle in get_bundles():
            hash_version = bundle_versions[bundle.name]
            bundle_path = bundle.get_path(hash_version)
            self.stdout.write("Removing bundle: %s\n" % bundle_path)
            try:
                os.remove(bundle_path)
            except:
                self.stderr.write("Could not remove bundle: %s\n" % bundle_path)

            if bundle.uglify_command:
                try:
                    if bundle.source_map_file_root and bundle.source_map_url_root:
                        os.remove('%s.%s.%s.map' % (os.path.join(bundle.source_map_file_root, bundle.bundle_filename), hash_version, bundle.bundle_type))
                    else:
                        os.remove('%s.map' % bundle_path)
                except:
                    self.stderr.write("Could not remove bundle source map: %s.map\n" % bundle_path)

        self.stdout.write("Removing bundles version file: %s\n" % bundles_settings.BUNDLES_VERSION_FILE)
        os.remove(bundles_settings.BUNDLES_VERSION_FILE)

        for _, single_file_output in bundles_settings.BUNDLES_SINGLE_FILES:
            self.stdout.write("Removing: %s\n" % single_file_output)
            try:
                os.remove(single_file_output)
            except:
                self.stderr.write("Could not remove single file: %s\n" % single_file_output)

        self.stdout.write("Done.\n")
