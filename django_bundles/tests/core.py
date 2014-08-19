from django.test import TestCase
from django.conf import settings


from django_bundles.core import Bundle
from django_bundles.processors import ExecutableProcessor


import os


class BundleConfTest(TestCase):
    def setUp(self):
        self.bundle = Bundle((
            'test_bundle', {
                'type': 'css',
                'files': (
                    'test*.css',
                    ('another.css', {
                        'processors': (
                            ('django_bundles.processors.ExecutableProcessor', {'command': 'cat {infile}'}),
                        ),
                    }),
                ),
                'media': 'screen',
                'files_root': os.path.join(os.path.dirname(__file__), 'files'),
                'processors': (
                    ('django_bundles.processors.ExecutableProcessor', {'command': 'cat {infile}'}),
                ),
            }
        ))


    def test_basic_conf(self):
        self.assertEqual(self.bundle.name, 'test_bundle')
        self.assertEqual(self.bundle.files_root, os.path.join(os.path.dirname(__file__), 'files'))
        self.assertEqual(self.bundle.media, 'screen')
        self.assertEqual(self.bundle.bundle_type, 'css')
        self.assertEqual(self.bundle.bundle_filename, 'test_bundle')
        self.assertEqual(self.bundle.bundle_url_root, settings.MEDIA_URL)
        self.assertEqual(self.bundle.bundle_file_root, os.path.join(os.path.dirname(__file__), 'files'))


    def test_processor_conf(self):
        self.assertEqual(len(self.bundle.processors), 1)
        self.assertTrue(isinstance(self.bundle.processors[0], ExecutableProcessor))
        self.assertEqual(self.bundle.processors[0].command, 'cat {infile}')


    def test_file_conf(self):
        self.assertEqual(len(self.bundle.files), 3)
        self.assertEqual([f.file_path for f in self.bundle.files], [
            os.path.join(os.path.dirname(__file__), 'files/test1.css'),
            os.path.join(os.path.dirname(__file__), 'files/test2.css'),
            os.path.join(os.path.dirname(__file__), 'files/another.css'),
        ])
        self.assertEqual([f.file_url for f in self.bundle.files], [
            os.path.join(settings.MEDIA_URL, 'test1.css'),
            os.path.join(settings.MEDIA_URL, 'test2.css'),
            os.path.join(settings.MEDIA_URL, 'another.css'),
        ])
