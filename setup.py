from distutils.core import setup

import sys
if sys.version < '3' or sys.version >= '4':
  print >> sys.stderr, 'Python 3 required'
  exit(1)

from rempy import __version__ as version
setup(
  name='rempy',
  version=version,
  description='Console reminder program inspired by remind',
  author='Evgeny Arshinov',
  author_email='earshinov@gmail.com',
  packages=['rempy', 'rempy.utils', 'rempy.contrib', 'rempy.contrib.deferrable'],
  provides=['rempy', 'rempy.contrib.deferrable'],
  scripts=['scripts/rem.py'],
  license='GPL-2',
  classifiers = [
    'Programming Language :: Python :: 3 :: Only'
  ]
)
