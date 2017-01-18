from django.test import TestCase


from django_bundles.utils import get_class


class GetClassTest(TestCase):
    def test_getting_class(self):
        cls = get_class('django.test.TestCase')
        cls2 = get_class('thisisnotaclass')
        cls3 = get_class('thisisnotaclass.alsothis')

        self.assertEqual(cls, TestCase)
        self.assertEqual(cls2, None)
        self.assertEqual(cls3, None)

