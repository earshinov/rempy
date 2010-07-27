import functools
import re


class TokenWithPosition(object):

  def __init__(self, string, pos):
    super(TokenWithPosition, self).__init__()
    self._string = string
    self._pos = pos

  def position(self):
    return self._pos

  def string(self):
    return self._string


  def __getattr__(self, name):
    attr = getattr(self._string, name)
    if callable(attr) and name != 'join':
      @functools.wraps(attr)
      def positionPropagator(*args, **kwargs):
        ret = attr(*args, **kwargs)
        if isinstance(ret, basestring):
          return TokenWithPosition(ret, self._pos)
        else:
          return ret
      return positionPropagator
    else:
      return attr

  def __getitem__(self, key):
    return TokenWithPosition(self._string[key], self._pos)


  def __cmp__(self, other):
    if isinstance(other, basestring):
      return cmp(self._string, other)
    else:
      return cmp(id(self), id(other))

  def __hash__(self):
    return hash(self._string)


  def __str__(self):
    return str(self._string)

  def __unicode__(self):
    return unicode(self._string)


NONSPACES_REGEXP = re.compile('(\S+)')
def splitWithPositions(string):
  pos = 0
  it = iter(re.split(NONSPACES_REGEXP, string))
  while True:
    space = it.next()
    pos += len(space)
    try:
      token = it.next()
    except StopIteration:
      break
    yield TokenWithPosition(token, pos)
    pos += len(token)
