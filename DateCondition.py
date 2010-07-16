#!/usr/bin/env python

import datetime
import itertools
import operator
import unittest


class PreciseDateCondition(object):

  def __init__(self, year, month, day):
    super(PreciseDateCondition, self).__init__()
    self.date = datetime.date(year, month, day)

  @staticmethod
  def fromDate(date):
    return PreciseDateCondition(date.year, date.month, date.day)


  def scan(self, startDate):
    if self.date >= startDate:
      yield self.date

  def scanBack(self, startDate):
    if self.date <= startDate:
      yield self.date


  class Test(unittest.TestCase):

    def setUp(self):
      self.startDate = datetime.date(2010, 7, 16)

    def test_eq(self):
      date = datetime.date(2010, 7, 16)
      self.__assertSuccess(date, PreciseDateCondition.fromDate(date).scan(self.startDate))

    def test_back_eq(self):
      date = datetime.date(2010, 7, 16)
      self.__assertSuccess(date, PreciseDateCondition.fromDate(date).scanBack(self.startDate))

    def test_less(self):
      date = datetime.date(2009, 1, 1)
      self.__assertFailure(date, PreciseDateCondition.fromDate(date).scan(self.startDate))

    def test_back_less(self):
      date = datetime.date(2009, 1, 1)
      self.__assertSuccess(date, PreciseDateCondition.fromDate(date).scanBack(self.startDate))

    def test_greater(self):
      date = datetime.date(2010, 12, 31)
      self.__assertSuccess(date, PreciseDateCondition.fromDate(date).scan(self.startDate))

    def test_back_greater(self):
      date = datetime.date(2010, 12, 31)
      self.__assertFailure(date, PreciseDateCondition.fromDate(date).scanBack(self.startDate))


    def __assertSuccess(self, date, ret):
      dates = list(ret)
      self.assertEqual(len(dates), 1)
      self.assertEqual(dates[0], date)

    def __assertFailure(self, date, ret):
      self.assertEqual(list(ret), [])


class SimpleDateCondition(object):

  def __init__(self, year=None, month=None, day=None):
    super(SimpleDateCondition, self).__init__()
    self.year = year
    self.month = month
    self.day = day

  def scan(self, startDate):
    for date in self.__scan(startDate): yield date

  def scanBack(self, startDate):
    for date in self.__scan(startDate, back=True): yield date


  def __scan(self, startDate, back=False):
    delta = 1 if not back else -1
    op = operator.lt if not back else operator.gt

    day = self.day
    if day is None:
      day = startDate.day

    month = self.month
    if month is None:
      month = startDate.month
      if op(day, startDate.day):
        month = month+1

    year = self.year
    if year is None:
      year = startDate.year
      if op(month, startDate.month) or month == startDate.month and op(day, startDate.day):
        year = year+1

    date = datetime.date(year, month, day)
    for _ in self.__yieldYears(date, back): yield _


  class __YieldTerminator(object):

    def __init__(self, nextDate = None):
      self.__nextDate = nextDate

    def nextDate(self):
      return self.__nextDate


  def __yieldYears(self, date, back):
    if self.year is not None:
      for _ in self.__yieldMonths(date, back):
        if not isinstance(_, self.__YieldTerminator):
          yield _
        #else:
        #  yield self.__YieldTerminator()
    else:
      break_ = False
      while not break_:
        for _ in self.__yieldMonths(date, back):
          if not isinstance(_, self.__YieldTerminator):
            yield _
          else:
            if _.nextDate() is not None:
              date = _.nextDate()
            else:
              month = self.month
              day = self.day
              if not back:
                month = month if month is not None else 1
                day = day if day is not None else 1
                date = datetime.date(date.year+1, month, day)
              elif day is not None:
                month = month if month is not None else 12
                date = datetime.date(date.year-1, month, day)
              elif month is None or month == 12:
                date = datetime.date(date.year, 1, 1) - datetime.timedelta(days=1)
              else:
                date = datetime.date(date.year-1, month+1, 1) - datetime.timedelta(days=1)


  def __yieldMonths(self, date, back):
    delta = 1 if not back else -1

    if self.month is not None:
      for _ in self.__yieldDays(date, back):
        if not isinstance(_, self.__YieldTerminator):
          yield _
        else:
          yield self.__YieldTerminator()
    else:
      break_ = False
      while not break_:
        for _ in self.__yieldDays(date, back):
          if not isinstance(_, self.__YieldTerminator):
            yield _
          else:
            nextDate = _.nextDate()
            if nextDate is not None:
              if date.year != nextDate.year:
                yield _
                break_ = True
              else:
                date = nextDate
            else:
              if not back and date.month == 12:
                day = self.day if self.day is not None else 1
                yield self.__YieldTerminator(nextDate=datetime.date(date.year+1, 1, day));
                break_ = True
              elif back and date.month == 1:
                day = self.day if self.day is not None else 31
                yield self.__YieldTerminator(nextDate=datetime.date(date.year-1, 12, day));
                break_ = True
              else:
                date = datetime.date(date.year, date.month + delta, date.day)
                break


  def __yieldDays(self, date, back):
    timedelta = datetime.timedelta(days=1)
    step = (lambda x: x + timedelta) if not back else (lambda x: x - timedelta)
    op = operator.gt if not back else operator.lt

    if self.day is not None:
      yield date
      yield self.__YieldTerminator()
    else:
      while True:
        yield date
        nextDate = step(date)
        if op(nextDate.month, date.month) or op(nextDate.year, date.year):
          yield self.__YieldTerminator(nextDate)
          break
        else:
          date = nextDate


  class Test(unittest.TestCase):

    def setUp(self):
      self.startDate = datetime.date(2010, 1, 10)

    def test_000(self):
      gen = SimpleDateCondition(None, None, None).scan(self.startDate)
      date = next(itertools.islice(gen, 365*2, None))
      self.assertEqual(date, datetime.date(2012, 1, 10))

    def test_001(self):
      gen = SimpleDateCondition(None, None, 17).scan(self.startDate)
      date = next(itertools.islice(gen, 13, None))
      self.assertEqual(date, datetime.date(2011, 2, 17))

    def test_011(self):
      dates = list(itertools.islice(SimpleDateCondition(None, 1, 8).scan(self.startDate), 2))
      self.assertEqual(dates[0], datetime.date(2011, 1, 8))
      self.assertEqual(dates[1], datetime.date(2012, 1, 8))

    def test_110(self):
      dates = list(SimpleDateCondition(2010, 1, None).scanBack(self.startDate))
      self.assertEqual(len(dates), 10)

    def test_100(self):
      dates = list(SimpleDateCondition(2010, None, None).scan(self.startDate))
      self.assertEqual(len(dates), 365-9)


if __name__ == '__main__':
  unittest.main()
