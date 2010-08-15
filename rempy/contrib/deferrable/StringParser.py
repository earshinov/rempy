# -*- coding: utf-8 -*-

'''Содержит класс L{DeferrableParser}'''

import datetime
import unittest

from rempy.StringParser import \
  StringParser, ReminderParser, ChainData, parseDate
from rempy.StringParser import DateNamedOptionParser


class DeferrableParser(StringParser):
  '''Класс-декоратор для разбора строки напоминалки с дополнительным параметром,
  который задаёт дату последнего выполнения события.  К опциям, которые
  поддерживает обёрнутый класс, добавляется длинная опция C{DONE <ISO Date>}

  Использование:
    - сконструировать объект
    - вызвать L{parse}
    - использовать возвращённое значение и значения, которые возвращает
      метод L{doneDate} и аналогичные геттеры в обёрнутом классе
  '''

  def __init__(self, chainFactory=ReminderParser, chainData=None):
    super(DeferrableParser, self).__init__()
    chainData = copy.copy(chainData) if chainData is not None else ChainData()
    self.doneParser = DateNamedOptionParser()
    chainData.namedOptionHandlers.update({'done': self.doneParser})
    self.chain = chainFactory(chainData=chainData)

  def parse(self, string):
    return self.chain.parse(string)

  def doneDate(self):
    '''Получить считанное значение даты последнего выполнения события в виде
    объекта класса C{datetime.date} или C{None}, если соответствующая опция
    отсутствовала в исходной строке
    '''
    return self.doneParser.value()

  def __getattr__(self, name):
    return getattr(self.chain, name)


  class Test(unittest.TestCase):
    '''Набор unit-тестов'''

    def setUp(self):
      self.parser = DeferrableParser()

    def test_undone(self):
      str = 'REM 2010-12-10 -5 +5 *5 FROM 2010-12-01 UNTIL 2010-12-31 MSG Message'
      self.parser.parse(str)
      self.assertEqual(self.parser.doneDate(), None)

    def test_done(self):
      str = 'REM 2010-12-10 -5 +5 *5 DONE 2010-12-20 UNTIL 2010-12-31 MSG Message'
      self.parser.parse(str)
      self.assertEqual(self.parser.doneDate(), datetime.date(2010, 12, 20))
