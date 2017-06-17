"""
Backup only the most important parts of a Postgres db 

example --
    # backup only guys named foo in the user table:
    import postgres
    pg = postgres.Dump(db, user, passwd, host, port)
    pg.select_dump('user', "SELECT * FROM user WHERE username='foo'")

tuning for restoring the db:
http://stackoverflow.com/questions/2094963/postgresql-improving-pg-dump-pg-restore-performance

other links:
http://blog.kimiensoftware.com/2011/05/compare-pg_dump-and-gzip-compression-241
"""
from __future__ import print_function
import re
import subprocess
import os, time
import tempfile


class Postgres(object):
    """wrapper to dump postgres tables"""

    # http://dbaspot.com/postgresql/348627-pg_dump-t-give-where-condition.html
    # http://docs.python.org/2/library/tempfile.html

    def __init__(self, dbname, username, password, host=None, port=5432, directory=None, **kwargs):
        self.tmp_files = set()
        self.outfile_count = 0

        if directory:
            if not os.path.exists(directory):
                os.makedirs(directory)

        else:
            directory = tempfile.mkdtemp(prefix="postgres-{}".format(time.strftime("%y%m%d%S")))

        self.directory = directory
        self.dbname = dbname
        self.username = username
        self.password = password
        self.host = host 
        self.port = port

        # make sure we have the needed stuff
        self._run_cmd("which psql")
        self._run_cmd("which pg_dump")
        self._run_cmd("which gzip")


    def __del__(self):
        # cleanup by getting rid of all the temporary files
        for tf in self.tmp_files:
            os.unlink(tf)

    def restore(self):
        """use the self.directory to restore a db

        NOTE -- this will only restore a database dumped with one of the methods
        of this class
        """

        # let's unzip all the files in the dir
        path = os.path.join(self.directory, '*')
        self._run_cmd('gunzip {}'.format(path), ignore_ret_code=True)

        sql_files = []
        for root, dirs, files in os.walk(self.directory):
            for f in files:
                if f.endswith('.sql'):
                    sql_files.append(f)

        sql_files.sort() # we want to go in the order the tables were dumped
        r = re.compile('\d{3,}_([^\.]+)')
        for f in sql_files:
            path = os.path.join(self.directory, f)
            m = r.match(f)
            if m:
                table = m.group(1)
                print('------- restoring table {}'.format(table))

                #psql_args = self._get_args('psql', '-X', '--echo-queries', '-f {}'.format(path))
                psql_args = self._get_args('psql', '-X', '--quiet', '-f {}'.format(path))
                self._run_cmd(' '.join(psql_args))

                # restore the sequence
                #self._restore_auto_increment(table)
                print('------- restored table {}'.format(table))

        return True

    def table_dump(self, table):
        """dump all the rows of the given table name"""
        if not table: raise ValueError("no table")

        print('------- dumping table {}'.format(table))
        pipes = ["gzip"]
        outfile_path = self._get_outfile_path(table)
        cmd = self._get_args(
            "pg_dump",
            "--table={}".format(table),
            #"--data-only",
            "--clean",
            "--no-owner",
            "--column-inserts",
        )
        cmd = ' '.join(cmd)
        cmd += ' | {}'.format(' | '.join(pipes))
        cmd += ' > {}'.format(outfile_path)

        self._run_cmd(cmd)
        print('------- dumped table {}'.format(table))
        return True

    def _get_file(self):
        '''
        return an opened tempfile pointer that can be used

        http://docs.python.org/2/library/tempfile.html
        '''
        f = tempfile.NamedTemporaryFile(delete=False)
        self.tmp_files.add(f.name)
        return f

    def _get_args(self, executable, *args):
        """compile all the executable and the arguments, combining with common arguments
        to create a full batch of command args"""
        args = list(args)
        args.insert(0, executable)
        if self.username:
            args.append("--username={}".format(self.username))
        if self.host:
            args.append("--host={}".format(self.host))
        if self.port:
            args.append("--port={}".format(self.port))

        args.append(self.dbname)
        #args.extend(other_args)
        return args

    def _get_env(self):
        """this returns an environment dictionary we want to use to run the command

        this will also create a fake pgpass file in order to make it possible for
        the script to be passwordless"""
        if hasattr(self, 'env'): return self.env

        # create a temporary pgpass file
        pgpass = self._get_file()
        # format: http://www.postgresql.org/docs/9.2/static/libpq-pgpass.html
        pgpass.write('*:*:*:{}:{}\n'.format(self.username, self.password))
        pgpass.close()
        self.env = dict(os.environ)
        self.env['PGPASSFILE'] = pgpass.name

        # we want to assure a consistent environment
        if 'PGOPTIONS' in self.env: del self.env['PGOPTIONS']
        return self.env

    def _run_cmd(self, cmd, ignore_ret_code=False, popen_kwargs=None):
        print(cmd)

        env = self._get_env()
        kwargs = {
            'shell': True,
            'env': env
        }
        if popen_kwargs: kwargs.update(popen_kwargs)
        pipe = subprocess.Popen(
            cmd,
            **kwargs
        )
        ret_code = pipe.wait()
        if not ignore_ret_code and ret_code > 0:
            raise RuntimeError('command {} did not execute correctly'.format(cmd))

        return pipe

    def _get_outfile_path(self, table):
        """return the path for a file we can use to back up the table"""
        self.outfile_count += 1
        outfile = os.path.join(self.directory, '{:03d}_{}.sql.gz'.format(self.outfile_count, table))
        return outfile

    def _run_queries(self, queries, *args, **kwargs):
        """run the queries

        queries -- list -- the queries to run
        return -- string -- the results of the query?
        """
        # write out all the commands to a temp file and then have psql run that file
        f = self._get_file()
        for q in queries:
            f.write("{};\n".format(q))
        f.close()

        psql_args = self._get_args('psql', '-X', '-f {}'.format(f.name))
        return self._run_cmd(' '.join(psql_args), *args, **kwargs)

    def _restore_auto_increment(self, table):
        """restore the auto increment value for the table to what it was previously"""
        query, seq_table, seq_column, seq_name = self._get_auto_increment_info(table)
        if query:
            queries = [query, "select nextval('{}')".format(seq_name)]
            return self._run_queries(queries)

    def _get_auto_increment_info(self, table):
        """figure out the the autoincrement value for the given table"""
        query = ''
        seq_table = ''
        seq_column = ''
        seq_name = ''
        find_query = "\n".join([
            "SELECT",
            "  t.relname as related_table,",
            "  a.attname as related_column,",
            "  s.relname as sequence_name",
            "FROM pg_class s",
            "JOIN pg_depend d ON d.objid = s.oid",
            "JOIN pg_class t ON d.objid = s.oid AND d.refobjid = t.oid",
            "JOIN pg_attribute a ON (d.refobjid, d.refobjsubid) = (a.attrelid, a.attnum)",
            "JOIN pg_namespace n ON n.oid = s.relnamespace",
            "WHERE",
            "  s.relkind = 'S'",
            "AND",
            "  n.nspname = 'public'",
            "AND",
            "  t.relname = '{}'".format(table)
        ])

        pipe = self._run_queries([find_query], popen_kwargs={'stdout': subprocess.PIPE})
        stdout, stderr = pipe.communicate()
        if stdout:
            try:
                m = re.findall('^\s*(\S+)\s*\|\s*(\S+)\s*\|\s*(\S+)\s*$', stdout, flags=re.MULTILINE)
                seq_table, seq_column, seq_name = m[1]
                # http://www.postgresql.org/docs/9.2/static/functions-sequence.html
                # http://www.postgresql.org/docs/9.2/static/functions-conditional.html
                query = "\n".join([
                    "SELECT",
                    "  setval('{}',".format(seq_name.strip()),
                    "  coalesce(max({}), 1),".format(seq_column.strip()),
                    "  max({}) IS NOT null)".format(seq_column.strip()),
                    "FROM \"{}\"".format(seq_table.strip())
                ])

            except IndexError:
                query = ''

        return query, seq_table, seq_column, seq_name


