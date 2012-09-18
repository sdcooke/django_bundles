from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from django_bundles.conf.bundles_settings import bundles_settings
from django_bundles.utils import expand_file_names
from django_bundles.processors import processor_library

import os

class Bundle(object):
    """
    Representation of a bundle of files - configuration looks like:

    ('master_css', {                                                    # bundle name
        'type': 'css',                                                  # bundle type (e.g. css, js) - also the bundle file extension
        'files': (                                                      # list of files to include
            'css/*.css',                                                # pattern matching is done
            ('css/more/test3.css', {
                # bundle file options (see BundleFile class)
            }),
            'less/test.less',
        ),
        'files_url_root': settings.MEDIA_URL,                           # Root URL for the files in the bundle [OPTIONAL - defaults to settings.MEDIA_URL]
        'files_root': settings.MEDIA_ROOT,                              # Root path for the files in the bundle [OPTIONAL - defaults to settings.MEDIA_ROOT]
        'media': None,                                                  # Media type (e.g. screen, print) [OPTIONAL - defaults to None]
        'bundle_url_root': settings.MEDIA_URL,                          # Root URL for the bundle file [OPTIONAL - defaults to files_url_root]
        'bundle_file_root': settings.MEDIA_ROOT,                        # Root path for the bundle file [OPTIONAL - defaults to files_root]
        'bundle_filename': 'master_css',                                # Filename for the bundle (without extension) [OPTIONAL - defaults to the bundle name]
        'processors': (                                                 # A list of post processors for the bundle (e.g. minifying) [OPTIONAL - defaults to the default processors for the bundle type]
            'django_bundles.contrib.processors.uglify.UglifyProcessor', # String,
            UglifyProcessor,                                            # Class,
            UglifyProcessor(),                                          # ...or instance
        )
    }),

    """
    def __init__(self, conf):
        """
        Initialize a bundle and it's BundleFiles based on a conf dict
        """
        self.name = conf[0]

        conf_dict = conf[1]

        # Basic settings and defaults
        self.bundle_type = conf_dict['type']
        files_url_root = conf_dict.get('files_url_root', settings.MEDIA_URL)
        files_root = conf_dict.get('files_root', settings.MEDIA_ROOT)
        self.media = conf_dict.get('media')
        self.bundle_url_root = conf_dict.get('bundle_url_root') or files_url_root
        self.bundle_file_root = conf_dict.get('bundle_file_root') or files_root
        self.bundle_filename = conf_dict.get('bundle_filename') or self.name

        # Build the list of BundleFiles
        self.files = []

        for fileconf in list(conf_dict['files']):
            path, extra = fileconf, None
            # Each file definition can be a string or tuple containing the path and the conf dict
            if isinstance(fileconf, (tuple, list)):
                path = fileconf[0]
                extra = fileconf[1]

            # Expand *s in filenames
            try:
                for filename in expand_file_names(path, files_root):
                    self.files.append(BundleFile(filename, files_root, files_url_root, self.media, self.bundle_type, extra=extra))
            except OSError:
                raise ImproperlyConfigured("Bundle %s - could not find file(s): %s" % (self.name, path))

        # Get the processors or use the default list
        if 'processors' in conf_dict:
            self.processors = processor_library.get_processors(conf_dict['processors'])
        else:
            self.processors = processor_library.get_default_postprocessors_for(self.bundle_type)

    def get_version(self):
        """
        Returns the current hash for this bundle
        """
        return get_bundle_versions().get(self.name)

    def get_url(self):
        """
        Return the filename of the bundled bundle
        """
        return '%s.%s.%s' % (os.path.join(self.bundle_url_root, self.bundle_filename), self.get_version(), self.bundle_type)

    def get_file_urls(self):
        """
        Return a list of file urls - will return a single item if settings.USE_BUNDLES is True
        """
        if bundles_settings.USE_BUNDLES:
            return [self.get_url()]
        return [bundle_file.file_url for bundle_file in self.files]

class BundleFile(object):
    """
    Representation of a file in a bundle - configuration looks like:

    {
        'processors': (                                                                         # List of preprocessors (run before the file is concatenated into the bundle) [OPTIONAL - defaults to the default preprocessors based on file type]
            'django_bundles.contrib.processors.django_template.DjangoTemplateProcessor',        # Same as post processors: String, Class or Instance
        ),
        'lint': True,                                                                           # Whether to lint the file [OPTIONAL - defaults to settings.BUNDLES_LINTING[...]['default']]
        'type': 'js',                                                                           # File type [OPTIONAL - defaults to file extension]
    }

    """
    def __init__(self, filename, files_root, url_root, media, bundle_type, extra=None):
        # basic settings
        self.file_path = os.path.join(files_root, filename)
        self.file_url = os.path.join(url_root, filename)
        self.media = media

        # file_type (or take from extension)
        if extra and 'type' in extra:
            self.file_type = extra['type']
        else:
            self.file_type = os.path.splitext(filename)[1][1:]

        # Lint setting and default
        if bundle_type in bundles_settings.BUNDLES_LINTING:
            self.lint = bundles_settings.BUNDLES_LINTING[bundle_type].get('default', False)
            if extra and 'lint' in extra:
                self.lint = extra['lint']
        else:
            self.lint = False

        # Preprocessors or get defaults
        if extra and 'processors' in extra:
            self.processors = processor_library.get_processors(extra['processors'])
        else:
            self.processors = processor_library.get_default_preprocessors_for(self.file_type)

class BundleManager(object):
    """
    Kind of like an ordered dictionary, but not as complicated
    """
    def __init__(self):
        self.keys = []
        self._items = {}

    def __setitem__(self, key, value):
        if key not in self._items:
            self.keys.append(key)
        self._items[key] = value

    def __getitem__(self, item):
        return self._items[item]

    def __iter__(self):
        for key in self.keys:
            yield self._items[key]

    def items(self):
        return ((key, self._items[key]) for key in self.keys)


_cached_bundles = None
def get_bundles():
    """
    Used to cache the bundle definitions rather than loading from config every time they're used
    """
    global _cached_bundles

    if not _cached_bundles:
        _cached_bundles = BundleManager()

        for bundle_conf in bundles_settings.BUNDLES:
            _cached_bundles[bundle_conf[0]] = Bundle(bundle_conf)

    return _cached_bundles

_cached_versions = None
def get_bundle_versions():
    """
    Used to cache the bundle versions rather than loading them from the bundle versions file every time they're used
    """
    global _cached_versions
    if not bundles_settings.BUNDLES_VERSION_FILE:
        _cached_versions = {}
    if _cached_versions is None:
        locs = {}
        try:
            execfile(bundles_settings.BUNDLES_VERSION_FILE, locs)
            _cached_versions = locs['BUNDLES_VERSIONS']
        except IOError:
            _cached_versions = {}
    return _cached_versions

def set_bundle_versions(bundles_versions):
    """
    Used to update the cached versions whilst building the bundle
    """
    global _cached_versions
    _cached_versions = bundles_versions

