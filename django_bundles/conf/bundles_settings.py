from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from django_bundles.conf import default_settings


class SettingsHelper(object):
    def __init__(self, user_settings, default_settings, optional_defaults):
        self.user_settings = user_settings
        self.default_settings = default_settings
        self.optional_defaults = set(optional_defaults)


    def __getattr__(self, name):
        if hasattr(self.user_settings, name):
            return getattr(self.user_settings, name)

        if name in self.optional_defaults:
            return getattr(self.default_settings, name)

        raise ImproperlyConfigured, "%s is a required setting for django_bundles" % name


bundles_settings = SettingsHelper(settings, default_settings, [
    'USE_BUNDLES',
    'DEVELOPMENT_BUNDLES',
    'DEFAULT_PREPROCESSORS',
    'DEFAULT_POSTPROCESSORS',
    'BUNDLES_LINTING',
    'BUNDLES_LINT_SUCCESS_OK',
    'BUNDLES_SINGLE_FILES',
    'BUNDLES_TAG_HTML',
    'GLOBAL_PRECOMPILE_DISABLE',
])
