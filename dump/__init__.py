import argparse

import postgres


__version__ = '0.0.2'


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
    parent_parser.add_argument("-U", "--username", dest="username", help="database user name")
    parent_parser.add_argument("-W", "--password", dest="password", help="database password")
    parent_parser.add_argument("-h", "--host", dest="host", default="localhost", help="database server host or socket directory")
    parent_parser.add_argument("-p", "--port", type=int, default=5432, dest="port", help="database server post")
    parent_parser.add_argument("--help", action="help", default=argparse.SUPPRESS, help="show this help message and exit")

    subparsers = parser.add_subparsers(dest="command", help="a sub command")
    backup_parser = subparsers.add_parser("backup", parents=[parent_parser], help="backup a PostgreSQL database", add_help=False)
    backup_parser.add_argument("-D", "--dir", "--directory", dest="directory", help="directory where the backup files should go")
    backup_parser.add_argument("tables", nargs="+")
    backup_parser.set_defaults(func=console_backup)

    restore_parser = subparsers.add_parser("restore", parents=[parent_parser], help="restore a PostgreSQL database", add_help=False)
    restore_parser.add_argument("-D", "--dir", "--directory", dest="directory", help="directory where the backup files are located")
    restore_parser.set_defaults(func=console_restore)

    args = parser.parse_args()
    ret_code = args.func(args)

    return ret_code

    if args.command == "backup":

        sub_parser.add_argument("-D", "--dir", dest="directory", help="directory where the backup files should go")
        sub_args = sub_parser.parse_args(command_args)
        #pout.v(sub_args, sub_args.dbname)

    elif args.command == "restore":

        sub_parser.add_argument("-D", "--dir", dest="directory", help="directory where the backup files are located")
        sub_args = sub_parser.parse_args(command_args)

    else:
        print "This should be the help part that prints out all the commands"


    ret_code = 0
    return ret_code

