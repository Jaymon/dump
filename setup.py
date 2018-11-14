#!/usr/bin/env python
# http://docs.python.org/distutils/setupscript.html
# http://docs.python.org/2/distutils/examples.html

from setuptools import setup, find_packages
import re
import os
from codecs import open


name = 'dump'
with open(os.path.join(name, "__init__.py"), encoding='utf-8') as f:
    version = re.search(r"^__version__\s*=\s*[\'\"]([^\'\"]+)", f.read(), flags=re.I | re.M).group(1)

long_description = ""
if os.path.isfile('README.rst'):
    with open('README.rst', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name=name,
    version=version,
    description='Wrapper around psql and pg_dump to make it easier to backup/restore a PostgreSQL database',
    long_description=long_description,
    author='Jay Marcyes',
    author_email='jay@marcyes.com',
    url='http://github.com/jaymon/{}'.format(name),
    packages=find_packages(),
    #py_modules=[name],
    license="MIT",
    #install_requires=[],
    tests_require=["dsnparse", "psycopg2", "testdata"],
    classifiers=[ # https://pypi.python.org/pypi?:action=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points = {
        'console_scripts': ['{} = {}.__main__:console'.format(name, name)]
    }
)
