import argparse

__version__ = '0.0.1'


def console():
    '''
    cli hook

    return -- integer -- the exit code
    '''
    parser = argparse.ArgumentParser(description="backup/restore PostgreSQL databases")
    parser.add_argument("-v", "--version", action='version', version="%(prog)s {}".format(__version__))
    #parser.add_argument("command", help="the command to run", default="", choices=set(["backup", "restore"]))
    args, command_args = parser.parse_known_args()

    sub_parser = argparse.ArgumentParser(description="backup a PostgreSQL database", add_help=False)
    sub_parser.add_argument("-d", "--dbname", dest="dbname", help="database name to connect to")
    sub_parser.add_argument("-U", "--username", dest="username", help="database user name")
    sub_parser.add_argument("-W", "--password", dest="password", help="database password")
    sub_parser.add_argument("-h", "--host", dest="host", default="localhost", help="database server host or socket directory")
    sub_parser.add_argument("-p", "--port", type=int, default=5432, dest="port", help="database server post")
    sub_parser.add_argument("--help", action="store_true", dest="help", help="show this help screen")

    if args.command == "backup":

        sub_parser.add_argument("-D", "--dir", dest="directory", help="directory where the backup files should go")
        sub_args = sub_parser.parse_args(command_args)
        pout.v(sub_args, sub_args.dbname)

    elif args.command == "restore":

        sub_parser.add_argument("-D", "--dir", dest="directory", help="directory where the backup files are located")
        sub_args = sub_parser.parse_args(command_args)

    else:
        print "This should be the help part that prints out all the commands"


    ret_code = 0
    return ret_code

#     if args.script:
#         s = Script(args.script)
#         try:
#             ret_code = s.run(command_args)
#             if not ret_code:
#                 ret_code = 0
# 
#         except Exception as e:
#             echo.exception(e)
#             ret_code = 1
# 
#     else:
#         basepath = os.getcwd()
#         print "Available scripts in {}:".format(basepath)
#         for root_dir, dirs, files in os.walk(basepath, topdown=True):
#             for f in fnmatch.filter(files, '*.py'):
#                 filepath = os.path.join(root_dir, f)
#                 s = Script(filepath)
#                 if s.is_cli():
#                     rel_filepath = s.call_path(basepath)
#                     print "\t{}".format(rel_filepath)
#                     desc = s.description
#                     if desc:
#                         for l in desc.split("\n"):
#                             print "\t\t{}".format(l)
# 
#                     print ""
# 
#     return ret_code

