from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured


from django_bundles.conf.bundles_settings import SettingsHelper


class ConfTest(TestCase):
    def setUp(self):
        class UserSettings():
            TEST1 = 'TEST1'

        class DefaultSettings():
            TEST1 = 'DEFAULT_TEST1'
            TEST2 = 'DEFAULT_TEST2'

        self.settings = SettingsHelper(UserSettings(), DefaultSettings(), ['TEST2'])


    def test_setting(self):
        self.assertEqual(self.settings.TEST1, 'TEST1')


    def test_default(self):
        self.assertEqual(self.settings.TEST2, 'DEFAULT_TEST2')


    def get_mandatory_setting(self):
        _ = self.settings.TEST3


    def test_mandatory(self):
        self.assertRaises(ImproperlyConfigured, self.get_mandatory_setting)