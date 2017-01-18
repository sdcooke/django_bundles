from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.utils import override_settings
from django.template import Template, Context


from django_bundles.core import BundleManager, Bundle


import os


TEST_FILES_PATH = os.path.join(os.path.dirname(__file__), 'files')


@override_settings(BUNDLES=(
    ('test_bundle', {
        'type': 'css',
        'files': (
            'test1.css',
            'test2.css',
        ),
        'media': 'screen',
        'files_root': TEST_FILES_PATH,
    })
),
BUNDLES_TAG_HTML={ 'css': '<link href="%(file_url)s" type="text/css" rel="stylesheet"%(attrs)s />', })
class RenderBundleTest(TestCase):
    def test_render_tag(self):
        self.assertRaises(ImproperlyConfigured, Template("""{% load django_bundles_tags %}{% render_bundle "does_not_exist" %}""").render, Context())


class GetBundlesTest(TestCase):
    @override_settings(BUNDLES=( ('test_bundle', { 'type': 'css', 'files': (), }), ))
    def test_get_bundles(self):
        context = Context()
        Template("""{% load django_bundles_tags %}{% get_bundles as test_bundles %}""").render(context)

        self.assertTrue(isinstance(context.get('test_bundles'), BundleManager))
        self.assertTrue(isinstance(context['test_bundles']['test_bundle'], Bundle))
