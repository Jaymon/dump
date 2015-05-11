"""
test dump

to run on the command line:
python -m unittest test_pout[.ClassTest[.test_method]]
"""
import unittest
import subprocess
import os
import random

import prom
import testdata


class Foo(prom.Orm):
    schema = prom.Schema(
        "foo",
        bar=prom.Field(int),
        #che=prom.Field(str)
    )

class Bar(prom.Orm):
    schema = prom.Schema(
        "bar",
        foo=prom.Field(int),
        #che=prom.Field(str)
    )


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
    @classmethod
    def setUpClass(cls):
        for interface_name, i in prom.get_interfaces().iteritems():
            i.delete_tables(disable_protection=True)

    def test_default_help(self):
        c = Client()
        self.assertLess(0, c.code)

    def test_full_table_backup_and_restore(self):
        directory = testdata.create_dir("full-table-backup")
        #directory = os.path.join("/", "tmp", "full-table-backup-{}".format(random.randint(1, 100000)))
        for x in range(100):
            f = Foo(bar=x)
            f.set()

        c = Client("backup --dbname vagrant --username vagrant --password vagrant --dir {} foo".format(directory))
        path, dirs, files = os.walk(directory).next()
        self.assertEqual(1, len(files))

        c = Client("restore --dbname vagrant --username vagrant --password vagrant --dir {}".format(directory))
        self.assertEqual(100, Foo.query.count())

        f = Foo(bar=101)
        f.set()
        self.assertLess(100, f.pk)

        self.setUpClass()
        c = Client("restore --dbname vagrant --username vagrant --password vagrant --dir {}".format(directory))
        self.assertEqual(100, Foo.query.count())

    def test_multi_table_backup(self):
        directory = testdata.create_dir("multi-table-backup")
        for x in range(10):
            f = Foo(bar=x)
            f.set()
            b = Bar(foo=x)
            b.set()

        c = Client("backup --dbname vagrant --username vagrant --password vagrant --dir {} foo bar".format(directory))
        pout.v(c.output)


if __name__ == '__main__':
    unittest.main()

