from django.test import TestCase


from django_bundles.utils.processes import run_process


import collections


class RunProcessTest(TestCase):

    def test_command_runs(self):
        stdin = 'TEST'
        output = ''.join(run_process('cat', stdin=stdin, iterate_stdin=False))

        self.assertEqual(stdin, output)


    def test_piped_command(self):
        stdin = "TEST1\nTEST2\nTEST1"

        output = ''.join(run_process('cat | grep "TEST1"', stdin=stdin, iterate_stdin=False))

        self.assertEqual(output, "TEST1\nTEST1\n")


    def test_stdin_iter(self):
        stdin_iter = ("TEST%s" % x for x in xrange(0, 3))

        output = ''.join(run_process('cat', stdin=stdin_iter))

        self.assertEqual(output, "TEST0TEST1TEST2")


    def test_to_close(self):
        with open(__file__, 'r') as f:
            collections.deque(run_process('cat', stdin='TEST', iterate_stdin=False, to_close=f), maxlen=0)
            self.assertTrue(f.closed)
