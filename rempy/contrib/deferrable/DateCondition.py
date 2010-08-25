# -*- coding: utf-8 -*-

'''Содержит класс L{DeferrableDateCondition}'''

import datetime
import itertools
import unittest

from rempy.DateCondition import DateCondition, SimpleDateCondition
from rempy.Runner import RunnerMode


class DeferrableDateCondition(DateCondition):
  '''Класс-декоратор, учитывающий дату последнего выполнения события.  Если
  в прошлом есть невыполненные событие, а в будущем в пределах числа дней для
  преждевременного предупреждения о событии - нет, сначала будет выведена дата
  последнего невыполненного события в прошлом.  Преждевременное предупреждение
  не учитывается, если запуск напоминалок происходит в режиме
  L{RunnerMode.EVENTS<rempy.Runner.RunnerMode.EVENTS>}.  Все даты, которые не
  превышают дату последнего выполнение, выводится не будут.  Реализовано только
  сканирование в направлении будущего.'''

  def __init__(self, cond, runnerMode, doneDate=None, advanceWarningValue=0):
    '''Конструктор

    @param cond: объект класса L{DateCondition<rempy.DateCondition.DateCondition>},
      который надо обернуть
    @param runnerMode: элемент «перечисления» L{RunnerMode<rempy.Runner.RunnerMode>},
      режим запуска напоминателей
    @param doneDate: объект класса C{datetime.date}, дата последнего выполнения.
      Если C{None}, считается, что событие ещё ни разу не выполнялось.
    @param advanceWarningValue: количество дней для преждевременного
      предупреждения о событии
    '''
    if advanceWarningValue < 0:
      raise ValueError('Advance warning value must not be negative')
    super(DeferrableDateCondition, self).__init__()
    self.cond = cond
    self.mode = runnerMode
    self.doneDate = doneDate
    self.adv = advanceWarningValue

  def scan(self, startDate):
    gen = iter(self.cond.scan(startDate))
    if self.doneDate is not None:
      gen = itertools.dropwhile(lambda date: self.doneDate >= date, gen)

    if self.mode == RunnerMode.REMIND:

      try:
        backDate = startDate - datetime.timedelta(days=1)
        lastUndone = iter(self.cond.scanBack(backDate)).next()
      except StopIteration:
        lastUndone = None
      if lastUndone is not None \
          and self.doneDate is not None \
          and self.doneDate >= lastUndone:
        lastUndone = None

      try:
        first = gen.next()
      except StopIteration:
        first = None

      if lastUndone is not None and (first is None or \
          first > startDate + datetime.timedelta(self.adv)):
        yield lastUndone
      if first is not None:
        yield first

    for date in gen:
      yield date

  def scanBack(self, startDate):
    '''Не реализовано: выбрасывает C{NotImplementedError}'''
    raise NotImplementedError()

  def __getattr__(self, name):
    return getattr(self.cond, name)


  class Test(unittest.TestCase):
    '''Набор unit-тестов'''

    def setUp(self):
      self.startDate = datetime.date(2010, 5, 12)
      self.simpleCond = SimpleDateCondition(2010, None, 14)

    def __simpleTest(self, firstReturnedDate, runnerMode=RunnerMode.REMIND, *args, **kwargs):
      cond = DeferrableDateCondition(self.simpleCond, runnerMode, *args, **kwargs)
      date = iter(cond.scan(self.startDate)).next()
      self.assertEquals(date, firstReturnedDate)


    def test_undone(self):
      self.__simpleTest(datetime.date(2010, 4, 14))

    def test_done(self):
      self.__simpleTest(datetime.date(2010, 5, 14),
        doneDate=datetime.date(2010, 4, 14))

    def test_doneEarly(self):
      self.__simpleTest(datetime.date(2010, 4, 14),
        doneDate=datetime.date(2010, 4, 12))

    def test_doneLate(self):
      self.__simpleTest(datetime.date(2010, 5, 14),
        doneDate=datetime.date(2010, 4, 16))

    def test_doneInFuture(self):
      self.__simpleTest(datetime.date(2010, 12, 14),
        doneDate=datetime.date(2010, 11, 14))

    def test_advanceWarning(self):
      self.__simpleTest(datetime.date(2010, 5, 14),
        advanceWarningValue=2)

    def test_eventsMode(self):
      self.__simpleTest(datetime.date(2010, 5, 14),
        RunnerMode.EVENTS)
