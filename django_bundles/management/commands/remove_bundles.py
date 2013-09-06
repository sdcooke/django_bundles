import os
from django.core.management.base import BaseCommand

from django_bundles.conf.bundles_settings import bundles_settings
from django_bundles.core import get_bundles, get_bundle_versions


def remove_bundles(command):
    bundle_versions = get_bundle_versions()

    for bundle in get_bundles():
        hash_version = bundle_versions[bundle.name]
        bundle_path = '%s.%s.%s' % (os.path.join(bundle.bundle_file_root, bundle.bundle_filename), hash_version, bundle.bundle_type)
        command.stdout.write("Removing bundle: %s\n" % bundle_path)
        try:
            os.remove(bundle_path)
        except:
            command.stderr.write("Could not remove bundle: %s\n" % bundle_path)

        if bundle.create_debug:
            debug_hash_version = bundle_versions['debug:' + bundle.name]

            bundle_debug_path = '%s.debug.%s.%s' % (os.path.join(bundle.bundle_file_root, bundle.bundle_filename), debug_hash_version, bundle.bundle_type)
            try:
                os.remove(bundle_debug_path)
            except:
                command.stderr.write("Could not remove debug bundle: %s\n" % bundle_debug_path)

    command.stdout.write("Removing bundles version file: %s\n" % bundles_settings.BUNDLES_VERSION_FILE)
    os.remove(bundles_settings.BUNDLES_VERSION_FILE)

    for _, single_file_output in bundles_settings.BUNDLES_SINGLE_FILES:
        command.stdout.write("Removing: %s\n" % single_file_output)
        try:
            os.remove(single_file_output)
        except:
            command.stderr.write("Could not remove single file: %s\n" % single_file_output)

    command.stdout.write("Done.\n")


class Command(BaseCommand):
    help = "Removes any created bundles"
    requires_model_validation = False

    def handle(self, *args, **options):
        remove_bundles(self)