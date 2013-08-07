from django.conf import settings

USE_BUNDLES = not settings.DEBUG

DEFAULT_PREPROCESSORS = {
    'less': [
        ('django_bundles.processors.ExecutableProcessor', {'command':'lessc %(infile)s %(outfile)s'}),
    ],
}

DEFAULT_POSTPROCESSORS = {
    'js': [
        ('django_bundles.processors.ExecutableProcessor', {'command':'uglifyjs -nc --unsafe -o %(outfile)s %(infile)s'}),
    ],
}

BUNDLES_LINTING = {}

BUNDLES_LINT_SUCCESS_OK = True

BUNDLES_SINGLE_FILES = ()

BUNDLES_TAG_HTML = {
    'js': '<script src="%(file_url)s"></script>',
    'css': '<link href="%(file_url)s" type="text/css" rel="stylesheet"%(attrs)s />',
    'less': '<link href="%(file_url)s" type="text/less" rel="stylesheet"%(attrs)s />',
}