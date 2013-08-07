from django.test import TestCase


from django_bundles.utils.files import expand_file_names, FileChunkGenerator


import os
import collections


class ExpandFileNamesTest(TestCase):
    def test_expand_file_names(self):
        current_dir = os.path.dirname(__file__)
        files_in_dir = os.listdir(current_dir)
        python_files_in_dir = [fn for fn in files_in_dir if fn[-3:] == '.py']

        expanded_file_list = expand_file_names("*.py", current_dir)

        self.assertEqual(expanded_file_list, python_files_in_dir)


class FileChunkGeneratorTest(TestCase):
    def test_contents(self):
        with open(__file__, 'r') as f:
            file_contents = f.read()

        with open(__file__, 'r') as f:
            g = FileChunkGenerator(f)

            file_contents_2 = ''
            for chunk in g:
                file_contents_2 += chunk

        self.assertEqual(file_contents, file_contents_2)

    def test_file_closes(self):
        with open(__file__, 'r') as f:
            g = FileChunkGenerator(f)

            collections.deque(g, maxlen=0)

            self.assertTrue(f.closed)

    def test_file_stays_open(self):
        with open(__file__, 'r') as f:
            g = FileChunkGenerator(f, close=False)

            collections.deque(g, maxlen=0)

            self.assertFalse(f.closed)
