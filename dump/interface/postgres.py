# -*- coding: utf-8 -*-
"""
Make backing up a postgres db a little easier to manage


tuning for restoring the db:
http://stackoverflow.com/questions/2094963/postgresql-improving-pg-dump-pg-restore-performance

other links:
http://blog.kimiensoftware.com/2011/05/compare-pg_dump-and-gzip-compression-241
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import re
import subprocess
import os, time
import tempfile
import logging


logger = logging.getLogger(__name__)


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
        self._run_cmd(["which", "psql"])
        self._run_cmd(["which", "pg_dump"])
        self._run_cmd(["which", "gzip"])


    def __del__(self):
        # cleanup by getting rid of all the temporary files
        for tf in self.tmp_files:
            os.unlink(tf)

    def restore(self):
        """use the self.directory to restore a db

        NOTE -- this will only restore a database dumped with one of the methods
        of this class
        """
        sql_files = []
        for root, dirs, files in os.walk(self.directory):
            for f in files:
                if f.endswith(".sql.gz"):
                    path = os.path.join(self.directory, f)
                    self._run_cmd(["gunzip", path])
                    sql_files.append(f.rstrip(".gz"))

                elif f.endswith('.sql'):
                    sql_files.append(f)

        sql_files.sort() # we want to go in the order the tables were dumped
        r = re.compile('\d{3,}_([^\.]+)')
        for f in sql_files:
            path = os.path.join(self.directory, f)
            m = r.match(f)
            if m:
                table = m.group(1)
                logger.info('------- restoring table {}'.format(table))

                #psql_args = self._get_args('psql', '-X', '--echo-queries', '-f {}'.format(path))
                psql_args = self._get_args('psql', '-X', '--quiet', '--file={}'.format(path))
                self._run_cmd(psql_args)

                logger.info('------- restored table {}'.format(table))

        return True

    def table_dump(self, table):
        """dump all the rows of the given table name"""
        if not table: raise ValueError("no table")

        cmds = []
        logger.info('------- dumping table {}'.format(table))
        cmd = self._get_args(
            "pg_dump",
            "--table={}".format(table),
            #"--data-only",
            "--clean",
            "--no-owner",
            "--column-inserts",
        )
        cmds.append((cmd, {}))

        outfile_path = self._get_outfile_path(table)
        cmds.append(('gzip > "{}"'.format(outfile_path), {"shell": True}))

        #cmd += ' | {}'.format(' | '.join(pipes))
        #cmd += ' > {}'.format(outfile_path)

        self._run_cmds(cmds)
        logger.info('------- dumped table {}'.format(table))
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
        pgpass.write('*:*:*:{}:{}\n'.format(self.username, self.password).encode("utf-8"))
        pgpass.close()
        self.env = dict(os.environ)
        self.env['PGPASSFILE'] = pgpass.name

        # we want to assure a consistent environment
        if 'PGOPTIONS' in self.env: del self.env['PGOPTIONS']
        return self.env

    def _run_cmds(self, cmds):

        pipes = []
        env = self._get_env()
        for args, kwargs in cmds:
            logger.debug("Running: {}".format(args))

            if "env" not in kwargs:
                kwargs["env"] = env

            if pipes:
                kwargs["stdin"] = pipes[-1].stdout

            kwargs["stdout"] = subprocess.PIPE

            pipes.append(subprocess.Popen(args, **kwargs))

        for i, pipe in enumerate(pipes):
            ret_code = pipe.wait()
            if ret_code > 0:
                raise IOError("Command {} exited with {}".format(cmds[i][0], ret_code))

    def _run_cmd(self, cmd, **kwargs):

        ignore_ret_code = kwargs.pop("ignore_ret_code", False)

        try:
            self._run_cmds([(cmd, kwargs)])

        except IOError as e:
            if ignore_ret_code:
                logger.warn(e, exc_info=True)
                pass
            else:
                raise

    def _get_outfile_path(self, table):
        """return the path for a file we can use to back up the table"""
        self.outfile_count += 1
        outfile = os.path.join(self.directory, '{:03d}_{}.sql.gz'.format(self.outfile_count, table))
        return outfile

