# -*- coding: utf-8 -*-

'''Функции и классы для работы со строками'''

import functools
import re


class TokenWithPosition(object):
  '''Класс, экземпляры которого ведут себя как строки, но при этом сохраняют
  дополнительный атрибут - позицию.  Может быть полезен, если к строке
  необходимо прикрепить, к примеру, её позицию в другой строке.

  Все методы строки, в свою очередь возвращающие строки, переопределяются, так
  что возвращаются объекты данного класса.  К каждому такому объекту
  прикрепляется то же значение позиции.  Исключением является метод join,
  который не переопределяется, так как сохранение позиции в этом случае
  смысла не имеет.'''

  def __init__(self, string, pos):
    '''Конструктор

    @param string: строка
    @param pos: позиция
    '''
    super(TokenWithPosition, self).__init__()
    self._string = string
    self._pos = pos

  def position(self):
    '''Получить позицию

    @returns: позиция, переданная в конструктор
    '''
    return self._pos

  def string(self):
    '''Получить строку

    @returns: строка, переданная в конструктор
    '''
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


_NONSPACES_REGEXP = re.compile('(\S+)')
def splitWithPositions(string):
  '''Разбить строку по пробельным символам и возвратить список объектов
  класса L{TokenWithPosition}, к каждому из которых прикреплена позиция
  в исходной строке

  @param string: строка
  @returns: Iterable по объектам класса L{TokenWithPosition}
  '''
  pos = 0
  it = iter(re.split(_NONSPACES_REGEXP, string))
  while True:
    space = it.next()
    pos += len(space)
    try:
      token = it.next()
    except StopIteration:
      break
    yield TokenWithPosition(token, pos)
    pos += len(token)
