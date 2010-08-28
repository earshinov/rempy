from distutils.core import setup

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
  scripts=['scripts/rem.py'],
  license='GPL-2'
)
