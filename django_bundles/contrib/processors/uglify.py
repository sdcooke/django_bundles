from django_bundles.processors import ExecutableProcessor
from django_bundles.conf.bundles_settings import bundles_settings

class UglifyProcessor(ExecutableProcessor):
    command = bundles_settings.BUNDLES_UGLIFY_COMMAND
