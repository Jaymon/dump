# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import argparse
import sys
import logging

from dump import __version__
from dump.interface import postgres


def console_backup(args):
    kwargs = vars(args)
    tables = kwargs.pop("tables")

    db = postgres.Postgres(**kwargs)
    for table in tables:
        db.table_dump(table)

    return 0


def console_restore(args):
    kwargs = vars(args)
    db = postgres.Postgres(**kwargs)
    db.restore()
    return 0


def console():
    '''
    cli hook

    return -- integer -- the exit code
    '''
    parser = argparse.ArgumentParser(description="backup/restore PostgreSQL databases", add_help=False)
    parser.add_argument("--version", action='version', version="%(prog)s {}".format(__version__))

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("-d", "--dbname", dest="dbname", help="database name to connect to")
    parent_parser.add_argument("-U", "--username", "--user", dest="username", help="database user name")
    parent_parser.add_argument("-W", "--password", dest="password", help="database password")
    parent_parser.add_argument(
        "-h", "--host", "--hostname",
        dest="host",
        default="localhost",
        help="database server host or socket directory"
    )
    parent_parser.add_argument("-p", "--port", type=int, default=5432, dest="port", help="database server post")
    parent_parser.add_argument(
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="show this help message and exit"
    )

    subparsers = parser.add_subparsers(dest="command", help="a sub command")
    subparsers.required = True # https://bugs.python.org/issue9253#msg186387
    backup_parser = subparsers.add_parser(
        "backup",
        parents=[parent_parser],
        help="backup a PostgreSQL database",
        add_help=False
    )
    backup_parser.add_argument(
        "-D", "--dir", "--directory",
        dest="directory",
        help="directory where the backup files should go"
    )
    backup_parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="Turn on debugging output"
    )
    backup_parser.add_argument("tables", nargs="+")
    backup_parser.set_defaults(func=console_backup)

    restore_parser = subparsers.add_parser(
        "restore",
        parents=[parent_parser],
        help="restore a PostgreSQL database",
        add_help=False
    )
    restore_parser.add_argument(
        "-D", "--dir", "--directory",
        dest="directory",
        help="directory where the backup files are located"
    )
    restore_parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="Turn on debugging output"
    )
    restore_parser.set_defaults(func=console_restore)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(format="[%(levelname).1s] %(message)s", level=logging.DEBUG, stream=sys.stdout)
    else:
        logging.basicConfig(format="[%(levelname).1s] %(message)s", level=logging.INFO, stream=sys.stdout)

    ret_code = args.func(args)
    return ret_code


if __name__ == "__main__":
    sys.exit(console())

