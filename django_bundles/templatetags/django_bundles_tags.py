from django import template

from django.core.exceptions import ImproperlyConfigured

from django_bundles.conf.bundles_settings import bundles_settings
from django_bundles.core import get_bundles

register = template.Library()


def _render_file(file_type, file_url, attrs=None):
    attr_string = ''
    if attrs:
        attr_string = ''.join(' %s="%s"' % x for x in attrs.iteritems())

    return bundles_settings.BUNDLES_TAG_HTML[file_type] % {
        'file_url': file_url,
        'attrs': attr_string,
    }


def _render_bundle(bundle_name):
    """
    Renders the HTML for a bundle in place - one HTML tag or many depending on settings.USE_BUNDLES
    """
    try:
        bundle = get_bundles()[bundle_name]
    except KeyError:
        raise ImproperlyConfigured("Bundle '%s' is not defined" % bundle_name)

    if bundle.use_bundle:
        return _render_file(bundle.bundle_type, bundle.get_url(), attrs=({'media':bundle.media} if bundle.media else {}))

    # Render files individually
    bundle_files = []

    for bundle_file in bundle.files:
        if bundle_file.precompile_in_debug:
            bundle_files.append(_render_file(bundle_file.bundle_type, bundle_file.precompile_url, attrs=({'media':bundle_file.media} if bundle.media else {})))
        else:
            bundle_files.append(_render_file(bundle_file.file_type, bundle_file.file_url, attrs=({'media':bundle_file.media} if bundle.media else {})))

    return '\n'.join(bundle_files)


@register.simple_tag
def render_bundle(bundle_name):
    return _render_bundle(bundle_name)


@register.assignment_tag(name='get_bundles')
def do_get_bundles():
    """
    Assigns the bundle definitions to a context variable
    """
    return get_bundles()
