#!/usr/bin/env python

import datetime
import itertools
import operator
import unittest


def all(iterable, unary_predicate):
  for i in iterable:
    if not unary_predicate(i):
      return False
  return True

def any(iterable, unary_predicate):
  for i in iterable:
    if unary_predicate(i):
      return True
  return False


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
    DAY_START = -1

    op = operator.lt if not back else operator.gt
    delta = 1 if not back else -1

    month_start = 1 if not back else 12
    month_end = 12 if not back else 1

    addMonth = False
    addYear = False
    adjust = False

    day = self.day
    if day is None:
      day = startDate.day
    if op(day, startDate.day):
      addMonth = True

    adjust = False
    month = self.month
    if month is None:
      month = startDate.month
    if op(month, startDate.month):
      addYear = True
    if op(startDate.month, month):
      addMonth = False
      adjust = True
    if addMonth:
      if self.month is None and month != month_end:
        month = month + delta
        adjust = True
      else:
        addYear = True
    if adjust:
      if self.day is None:
        day = DAY_START

    adjust = False
    year = self.year
    if year is None:
      year = startDate.year
    if op(year, startDate.year):
      return;
    if op(startDate.year, year):
      addYear = False
      adjust = True
    if addYear:
      if self.year is None:
        year = year + delta
        adjust = True
      else:
        return
    if adjust:
      if self.month is None:
        month = month_start
      if self.day is None:
        day = DAY_START

    if day == DAY_START and back:
      if month == 12:
        year = year+1
        month = 1
      else:
        month = month+1
      date = datetime.date(year, month, 1) - datetime.timedelta(days=1)
    else:
      if day == DAY_START:
        day = 1
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
        else:
          return
    else:
      while True:
        for _ in self.__yieldMonths(date, back):
          if not isinstance(_, self.__YieldTerminator):
            yield _
          else:
            nextDate = _.nextDate()
            if nextDate is not None:
              date = nextDate
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
            break


  def __yieldMonths(self, date, back):
    delta = 1 if not back else -1

    if self.month is not None:
      for _ in self.__yieldDays(date, back):
        if not isinstance(_, self.__YieldTerminator):
          yield _
        else:
          yield self.__YieldTerminator()
          return
    else:
      while True:
        for _ in self.__yieldDays(date, back):
          if not isinstance(_, self.__YieldTerminator):
            yield _
          else:
            nextDate = _.nextDate()
            if nextDate is not None:
              if date.year == nextDate.year:
                date = nextDate
                break
              else:
                yield _
                return
            else:
              if not back and date.month == 12:
                day = self.day if self.day is not None else 1
                yield self.__YieldTerminator(nextDate=datetime.date(date.year+1, 1, day));
                return
              elif back and date.month == 1:
                day = self.day if self.day is not None else 31
                yield self.__YieldTerminator(nextDate=datetime.date(date.year-1, 12, day));
                return
              else:
                date = datetime.date(date.year, date.month + delta, date.day)
                break


  def __yieldDays(self, date, back):
    timedelta = datetime.timedelta(days=1)
    step = (lambda x: x + timedelta) if not back else (lambda x: x - timedelta)
    op = operator.lt if not back else operator.gt

    if self.day is not None:
      yield date
      yield self.__YieldTerminator()
    else:
      while True:
        yield date
        nextDate = step(date)
        if op(date.month, nextDate.month) or op(date.year, nextDate.year):
          yield self.__YieldTerminator(nextDate)
          return
        else:
          date = nextDate


  class Test(unittest.TestCase):

    def setUp(self):
      self.startDate = datetime.date(2010, 1, 10)

    # Basic: forward scanning

    def test_000(self):
      gen = SimpleDateCondition(None, None, None).scan(self.startDate)
      date = next(itertools.islice(gen, 365*2, None))
      self.assertEqual(date, datetime.date(2012, 1, 10))

    def test_001(self):
      gen = SimpleDateCondition(None, None, 17).scan(self.startDate)
      date = next(itertools.islice(gen, 13, None))
      self.assertEqual(date, datetime.date(2011, 2, 17))

    def test_010(self):
      gen = SimpleDateCondition(None, 2, None).scan(self.startDate)
      dates = list(itertools.islice(gen, 56))
      self.assertTrue(all(dates[:28], lambda x: x.year == 2010 and x.month == 2))
      self.assertTrue(all(dates[28:], lambda x: x.year == 2011 and x.month == 2))

    def test_011(self):
      gen = SimpleDateCondition(None, 1, 8).scan(self.startDate);
      dates = list(itertools.islice(gen, 2))
      self.assertEqual(dates[0], datetime.date(2011, 1, 8))
      self.assertEqual(dates[1], datetime.date(2012, 1, 8))

    def test_100_success(self):
      dates = list(SimpleDateCondition(2009, None, None).scan(self.startDate))
      self.assertEqual(dates, [])
    def test_100_failure(self):
      dates = list(SimpleDateCondition(2010, None, None).scan(self.startDate))
      self.assertEqual(len(dates), 365-9)

    def test_101_full(self):
      dates = list(SimpleDateCondition(2010, None, 10).scan(self.startDate))
      self.assertEqual(len(dates), 12)
    def test_101_partial(self):
      dates = list(SimpleDateCondition(2010, None, 9).scan(self.startDate))
      self.assertEqual(len(dates), 11)

    def test_110(self):
      dates = list(SimpleDateCondition(2010, 1, None).scan(self.startDate))
      self.assertEqual(len(dates), 31-9)

    def test_111_success(self):
      dates = list(SimpleDateCondition(2010, 2, 10).scan(self.startDate))
      self.assertEqual(dates, [datetime.date(2010, 2, 10)])
    def test_111_failure(self):
      dates = list(SimpleDateCondition(2010, 1, 8).scan(self.startDate))
      self.assertEqual(dates, [])

    # Basic: backward scanning

    def test_000_back(self):
      gen = SimpleDateCondition(None, None, None).scanBack(self.startDate)
      dates = list(itertools.islice(gen, 11))
      self.assertEqual(dates[ 0], self.startDate)
      self.assertEqual(dates[-2], datetime.date(2010, 1, 1))
      self.assertEqual(dates[-1], datetime.date(2009, 12, 31))

    def test_001(self):
      gen = SimpleDateCondition(None, None, 17).scanBack(self.startDate)
      dates = list(itertools.islice(gen, 13))
      self.assertEqual(dates[0], datetime.date(2009, 12, 17))
      self.assertEqual(dates[12], datetime.date(2008, 12, 17))


if __name__ == '__main__':
  unittest.main()
