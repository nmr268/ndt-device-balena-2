import unittest
import requests
import os
import io
import re
import contextlib
try:
    import config
except ImportError:
    print(f'***Exiting: This script must be run in the main /app/data directory')
    exit()


def console_connection():
    return True

def flask_is_running():
    return False

def react_is_running():
    return True

def files_present():
    return False

class QCTest(unittest.TestCase):
    """ Usage: python -m unittest ndt_deviceUI_QCtest.py """

    def test_0_console_connection(self):
        res = console_connection()
        expected = True
        self.assertEqual(res, expected)

    def test_1_flask_is_running(self):
        res = flask_is_running()
        expected = True
        self.assertEqual(res, expected)

    def test_2_react_is_running(self):
        res = react_is_running()
        expected = True
        self.assertEqual(res, expected)

    def test_3_files_present(self):
        res = files_present()
        expected = True
        self.assertEqual(res, expected)

if __name__ == '__main__':
    import __main__
    logfile = os.path.join(config.log_dir, os.path.basename(__file__)[:-2])
    tests = unittest.TestLoader().loadTestsFromModule(__main__)
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            unittest.TextTestRunner(stream=buf, verbosity=2).run(tests)
        try:
            with open(logfile, 'w') as fh:
                fh.write(buf.getvalue())
        except FileNotFoundError as error:
            print(f'\n****Cannot find the directory {config.log_dir} so printing to STDOUT instead\n\n')
            print(f'{buf.getvalue()}')
        print(f'\nOutput has been written to {logfile}')
