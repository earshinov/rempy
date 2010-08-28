import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

import sys
if sys.version < '2.6' or sys.version > '3':
  print >> sys.stderr, 'Python 2.x, x >= 6 required'
  exit(1)

from rempy import __version__ as version
setup(
  name='rempy',
  version=version,
  description='Console reminder program inspired by remind',
  author='Eugene Arshinov',
  author_email='earshinov@gmail.com',
  packages=['rempy', 'rempy.utils', 'rempy.contrib', 'rempy.contrib.deferrable'],
  provides=['rempy', 'rempy.contrib.deferrable'],
  license='GPL-2',

  entry_points={
    'console_scripts': ['rem.py = rempy.Runner:main'],
  },
  extras_require={
    'human-readable-dates': ['parsedatetime'],
  },
  test_suite='rempy.tests',
)
