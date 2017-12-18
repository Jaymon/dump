# -*- coding: utf-8 -*-
"""
test dump

to run on the command line:
python -m unittest test_pout[.ClassTest[.test_method]]
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import unittest
import subprocess
import os
import random

import testdata
import dsnparse
import psycopg2
import psycopg2.extras


class Connection(object):
    instance = None

    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = cls(os.environ["DUMP_DSN"])
        return cls.instance

    def __init__(self, dsn):
        self.dsn = dsnparse.parse(dsn)

        self.dbname = self.dsn.dbname
        self.user = self.dsn.username
        self.password = self.dsn.password
        self.host = self.dsn.hostname
        self.port = self.dsn.port

        if self.dsn.scheme.startswith("postgres"):
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
            self.conn.autocommit = True
        else:
            raise ValueError("{} is unsupported".format(self.dsn.scheme))

    def close(self):
        self.conn.close()
        type(self).instance = None


class Foo(object):
    table_name = "foo"

    fields = [
        ("_id", "BIGSERIAL PRIMARY KEY"),
        ("bar", "INTEGER"),
    ]

    def __init__(self, **fields):
        for k, v in fields.items():
            setattr(self, k, v)

    def delete(self):
        query_str = 'DROP TABLE IF EXISTS "{}" CASCADE'.format(self.table_name)
        ret = self.query(query_str, ignore_result=True)

    def install(self):
        self.delete()
        query_str = []
        query_str.append('CREATE TABLE "{}" ('.format(self.table_name))

        query_fields = []
        for field_name, field in self.fields:
            query_fields.append('  {} {}'.format(field_name, field))

        query_str.append(",\n".join(query_fields))
        query_str.append(')')
        query_str = "\n".join(query_str)
        self.query(query_str, ignore_result=True)

    def count(self):
        ret = self.query('SELECT COUNT(*) FROM "{}"'.format(self.table_name))
        return int(ret[0]['count'])

    def save(self):
        field_names = []
        field_formats = []
        query_vals = []
        for k, _ in self.fields:
            try:
                v = getattr(self, k)
                query_vals.append(v)
                field_names.append(k)
            except AttributeError: pass

        #query_str = 'INSERT INTO {} ({}) VALUES ({}) RETURNING {}'.format(
        query_str = 'INSERT INTO "{}" ("{}") VALUES ({}) RETURNING "_id"'.format(
            self.table_name,
            '", "'.join(field_names),
            ', '.join(['%s'] * len(field_names)),
        )

        return self.query(query_str, query_vals)[0]["_id"]

    def query(self, query_str, query_vals=[], **kwargs):
        ret = None
        cur = Connection.get_instance().conn.cursor()
        if query_vals:
            cur.execute(query_str, query_vals)
        else:
            cur.execute(query_str)

        q = query_str.lower()
        if not kwargs.get("ignore_result", False):
            ret = cur.fetchall()
        return ret

    def close(self):
        Connection.get_instance().close()


class Bar(Foo):
    table_name = "bar"

    fields = [
        ("_id", "BIGSERIAL PRIMARY KEY"),
        ("foo", "INTEGER"),
    ]


class Client(object):
    """makes running a command nice and easy for easy peasy testing"""
    @property
    def files(self):
        for path, dirs, files in os.walk(self.directory):
            return [os.path.join(path, f) for f in files]
        #return files

    def __init__(self):
        self.code = 0
        self.output = ""
        self.directory = testdata.create_dir()

        conn = Connection.get_instance()
        self.arg_str = " ".join([
            "--dbname={}".format(conn.dbname),
            "--username={}".format(conn.user),
            "--password={}".format(conn.password),
            "--host={}".format(conn.host),
            "--port={}".format(conn.port),
            "--dir={}".format(self.directory),
            "--debug",
        ])

    def run(self, arg_str):
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

    def backup(self, *tables):
        subcommand = "backup"
        arg_str = "{} {} {}".format(subcommand, self.arg_str, " ".join(tables))
        return self.run(arg_str)

    def restore(self):
        subcommand = "restore"
        arg_str = "{} {}".format(subcommand, self.arg_str)
        return self.run(arg_str)


class DumpTest(unittest.TestCase):
    def setUp(self):
        Foo().install()
        Bar().install()

    def test_default_help(self):
        c = Client()
        c.run("")
        self.assertLess(0, c.code)

    def test_table_not_exist(self):
        Foo().delete()
        c = Client()
        c.backup(Foo.table_name)
        self.assertEqual(1, c.code, c.output)

    def test_full_table_backup_and_restore(self):
        for x in range(100):
            f = Foo(bar=x)
            _id = f.save()
            self.assertLess(0, _id)

        self.assertEqual(100, Foo().count())

        c = Client()
        c.backup(Foo.table_name)
        self.assertEqual(1, len(c.files))
        for path in c.files:
            self.assertLess(0, os.path.getsize(path))

        c.restore()
        self.assertEqual(100, Foo().count())

        f = Foo(bar=101)
        pk = f.save()
        self.assertLess(100, pk)


        self.setUp()
        c.restore()
        self.assertEqual(100, Foo().count())

    def test_multi_table_backup(self):
        count = 10
        for x in range(count):
            f = Foo(bar=x)
            f.save()
            b = Bar(foo=x)
            b.save()

        self.assertEqual(count, Foo().count())
        self.assertEqual(count, Bar().count())

        c = Client()
        c.backup(Foo.table_name, Bar.table_name)

        self.setUp()
        c.restore()
        self.assertEqual(count, Foo().count())
        self.assertEqual(count, Bar().count())


if __name__ == '__main__':
    unittest.main()

