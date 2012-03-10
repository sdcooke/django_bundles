from django.conf import settings

USE_BUNDLES = not settings.DEBUG

DEFAULT_PREPROCESSORS = {
    'less': [
        'django_bundles.contrib.processors.less.LessProcessor',
    ],
}

DEFAULT_POSTPROCESSORS = {
    'js': [
        'django_bundles.contrib.processors.uglify.UglifyProcessor',
    ],
}

BUNDLES_LINTING = {}