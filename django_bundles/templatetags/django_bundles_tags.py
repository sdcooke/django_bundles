from django import template
from django.template.loader import render_to_string

from django.core.exceptions import ImproperlyConfigured

from django_bundles.conf.bundles_settings import bundles_settings
from django_bundles.core import get_bundles

register = template.Library()

@register.simple_tag
def render_bundle(bundle_name):
    """
    Renders the HTML for a bundle in place - one HTML tag or many depending on settings.USE_BUNDLES
    """
    try:
        bundle = get_bundles()[bundle_name]
    except KeyError:
        raise ImproperlyConfigured("Bundle '%s' is not defined" % bundle_name)

    if bundles_settings.USE_BUNDLES:
        # Render one tag
        context = {
            'file_url': bundle.get_url(),
        }
        if bundle.media:
            context['attrs'] = { 'media': bundle.media }
        return render_to_string('django_bundles/%s.html' % bundle.bundle_type, context)

    # Render files individually
    bundle_files = []

    for bundle_file in bundle.files:
        context = {
            'file_url': bundle_file.file_url
        }
        if bundle_file.media:
            context['attrs'] = { 'media': bundle_file.media, }
        bundle_files.append(render_to_string('django_bundles/%s.html' % bundle_file.file_type, context))

    return '\n'.join(bundle_files)

if hasattr(register, 'assignment_tag'):
    @register.assignment_tag(name='get_bundles')
    def do_get_bundles():
        """
        Assigns the bundle definitions to a context variable
        """
        return get_bundles()
