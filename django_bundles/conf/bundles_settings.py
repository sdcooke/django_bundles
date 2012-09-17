from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from django_bundles.conf import default_settings

class SettingsHelper(object):
    USE_BUNDLES = getattr(settings, 'USE_BUNDLES', default_settings.USE_BUNDLES)

    DEFAULT_PREPROCESSORS = getattr(settings, 'DEFAULT_PREPROCESSORS', default_settings.DEFAULT_PREPROCESSORS)

    DEFAULT_POSTPROCESSORS = getattr(settings, 'DEFAULT_POSTPROCESSORS', default_settings.DEFAULT_POSTPROCESSORS)

    BUNDLES_LINTING = getattr(settings, 'BUNDLES_LINTING', default_settings.BUNDLES_LINTING)

    BUNDLES_LINT_SUCCESS_OK = getattr(settings, 'BUNDLES_LINT_SUCCESS_OK', default_settings.BUNDLES_LINT_SUCCESS_OK)

    BUNDLES_SINGLE_FILES = getattr(settings, 'BUNDLES_SINGLE_FILES', default_settings.BUNDLES_SINGLE_FILES)

    BUNDLES_OVERRIDE = getattr(settings, 'BUNDLES_OVERRIDE', default_settings.BUNDLES_OVERRIDE)

    def __getattr__(self, name):
        if hasattr(settings, name):
            return getattr(settings, name)
        raise ImproperlyConfigured, "%s is a required setting for django_bundles" % name

bundles_settings = SettingsHelper()
