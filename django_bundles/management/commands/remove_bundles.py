import os
from django.core.management.base import BaseCommand

from django_bundles.conf.bundles_settings import bundles_settings
from django_bundles.core import get_bundles, get_bundle_versions

class Command(BaseCommand):
    help = "Removes any created bundles"

    def handle(self, *args, **options):

        bundle_versions = get_bundle_versions()

        for bundle in get_bundles():
            hash_version = bundle_versions[bundle.name]
            bundle_path = '%s.%s.%s' % (os.path.join(bundle.bundle_file_root, bundle.bundle_filename), hash_version, bundle.bundle_type)
            self.stdout.write("Removing bundle: %s\n" % bundle_path)
            os.remove(bundle_path)

        self.stdout.write("Removing bundles version file: %s\n" % bundles_settings.BUNDLES_VERSION_FILE)
        os.remove(bundles_settings.BUNDLES_VERSION_FILE)

        for _, single_file_output in bundles_settings.BUNDLES_SINGLE_FILES:
            self.stdout.write("Removing: %s\n" % single_file_output)
            os.remove(single_file_output)

        self.stdout.write("Done.\n")
