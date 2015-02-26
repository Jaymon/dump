# Dump

Python wrapper around psql and pg_dump to make it easier to backup/restore a PostgreSQL database.


## Backup

You backup per table:

    dump backup --dbname=... --username=...  --password=... --dir /some/base/path table1 table2 ...


## Restore

You can restore the entire backup directory:

    dump restore --dbname=... --username=...  --password=... --dir /some/base/path


## Install

Use pip:

    pip install dump


## License

MIT

