"""
test dump

to run on the command line:
python -m unittest test_pout[.ClassTest[.test_method]]
"""
import unittest
import subprocess
import os

class Client(object):
    """makes running a command nice and easy for easy peasy testing"""
    def __init__(self, arg_str=""):
        self.code = 0
        self.output = ""
        self.run(arg_str)

    def run(self, arg_str=""):
        cmd = "python -m dump {}".format(arg_str)

        try:
            self.output = subprocess.check_output(
                cmd,
                shell=True,
                stderr=subprocess.STDOUT,
                cwd=os.curdir
            )

        except subprocess.CalledProcessError as e:
            self.code = e.returncode
            self.output = e.output


class DumpTest(unittest.TestCase):
    def test_default_help(self):
        c = Client()
        self.assertLess(0, c.code)

    def test_backup(self):
        c = Client("backup --dbname vagrant --username vagrant --password vagrant --dir /tmp")
        pout.v(c.output)


if __name__ == '__main__':
    unittest.main()

