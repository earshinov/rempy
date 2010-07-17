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


def lastDayOfMonth(year, month):
      if month == 12:
        year = year+1
        month = 1
      else:
        month = month+1
      return datetime.date(year, month, 1) - datetime.timedelta(days=1)


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

    op = operator.lt if not back else operator.gt
    delta = 1 if not back else -1

    month_start = 1 if not back else 12
    month_end = 12 if not back else 1


    class EmptyResultException(Exception):
      pass

    def addYear(year):
      if self.year is None:
        return year + delta
      else:
        raise EmptyResultException

    def addMonth(year, month):
      if self.month is None:
        if month == month_end:
          return (addYear(year), month_start)
        else:
          return (year, month + delta)
      else:
        return (addYear(year), month)


    try:
      year = self.year
      if year is None:
        year = startDate.year
      elif op(year, startDate.year):
        return

      atStartDate = (year == startDate.year)
      month = self.month
      if month is None:
        if atStartDate:
          month = startDate.month
        else:
          month = month_start
      elif op(month, startDate.month) and year == startDate.year:
        year = addYear(year)

      atStartDate = (year == startDate.year and month == startDate.month)
      day = self.day
      if day is None:
        if atStartDate:
          day = startDate.day
        else:
          day = 1 if not back else lastDayOfMonth(year, month).day
      elif op(day, startDate.day) and atStartDate:
        (year, month) = addMonth(year, month)
    except EmptyResultException:
      return


    date = datetime.date(year, month, day)
    daygen = self.__dayGenerator(date, back) if self.day is None \
      else self.__fixedDayGenerator(date)
    mongen = self.__monthGenerator(daygen, date, back) if self.month is None \
      else self.__fixedMonthGenerator(daygen, date)
    yeargen = self.__yearGenerator(mongen, date, back) if self.year is None \
      else self.__fixedYearGenerator(mongen, date)
    for date in yeargen: yield date


  def __fixedYearGenerator(self, monthGenerator, date):
    for _ in monthGenerator:
      if _ is None:
        return
      else:
        yield _

  def __yearGenerator(self, monthGenerator, date, back):
    year = date.year
    while True:
      for _ in monthGenerator:
        if _ is None:
          year += 1 if not back else -1
          monthGenerator.send(year)
        else:
          yield _

  def __fixedMonthGenerator(self, dayGenerator, date):
    for _ in dayGenerator:
      if _ is None:
        year = (yield _); yield None
        assert year is not None
        dayGenerator.send((year, date.month))
      else:
        yield _

  def __monthGenerator(self, dayGenerator, date, back):
    delta = 1 if not back else -1
    month_start = 1 if not back else 12
    month_end = 12 if not back else 1

    year = date.year
    month = date.month
    for _ in dayGenerator:
      if _ is None:
        if month != month_end:
          month += delta
        else:
          year = (yield _); yield None
          assert year is not None
          month = month_start
        dayGenerator.send((year, month))
      else:
        yield _

  def __fixedDayGenerator(self, date):
    (year, month, day) = (date.year, date.month, date.day)
    while True:
      yield datetime.date(year, month, day)
      (year, month) = (yield None); yield None

  def __dayGenerator(self, date, back):
    timedelta = datetime.timedelta(days=1)
    step = (lambda x: x + timedelta) if not back else (lambda x: x - timedelta)

    while True:
      yield date
      nextDate = step(date)
      if date.month != nextDate.month:
        (year, month) = (yield None); yield None
        if year != nextDate.year or month != nextDate.month:
          date = datetime.date(year, month, 1) if not back \
            else lastDayOfMonth(year, month)
          continue
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
      dates = list(SimpleDateCondition(2010, None, None).scan(self.startDate))
      self.assertEqual(len(dates), 365-9)
    def test_100_failure(self):
      dates = list(SimpleDateCondition(2009, None, None).scan(self.startDate))
      self.assertEqual(dates, [])

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
      dates = list(SimpleDateCondition(2011, 2, 10).scan(self.startDate))
      self.assertEqual(dates, [datetime.date(2011, 2, 10)])
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

    def test_001_back(self):
      gen = SimpleDateCondition(None, None, 17).scanBack(self.startDate)
      dates = list(itertools.islice(gen, 13))
      self.assertEqual(dates[0], datetime.date(2009, 12, 17))
      self.assertEqual(dates[12], datetime.date(2008, 12, 17))

    def test_010_back(self):
      gen = SimpleDateCondition(None, 2, None).scanBack(self.startDate)
      dates = list(itertools.islice(gen, 56))
      self.assertTrue(all(dates[:28], lambda x: x.year == 2009 and x.month == 2))
      self.assertTrue(all(dates[28:], lambda x: x.year == 2008 and x.month == 2))

    def test_011_back(self):
      gen = SimpleDateCondition(None, 1, 8).scanBack(self.startDate);
      dates = list(itertools.islice(gen, 2))
      self.assertEqual(dates[0], datetime.date(2010, 1, 8))
      self.assertEqual(dates[1], datetime.date(2009, 1, 8))

    def test_100_back_success(self):
      dates = list(SimpleDateCondition(2010, None, None).scanBack(self.startDate))
      self.assertEqual(len(dates), 10)
    def test_100_back_failure(self):
      dates = list(SimpleDateCondition(2011, None, None).scanBack(self.startDate))
      self.assertEqual(dates, [])

    def test_101_back_full(self):
      dates = list(SimpleDateCondition(2009, None, 10).scanBack(self.startDate))
      self.assertEqual(len(dates), 12)
    def test_101_back_partial(self):
      dates = list(SimpleDateCondition(2010, None, 10).scanBack(self.startDate))
      self.assertEqual(dates, [self.startDate])

    def test_110_back(self):
      dates = list(SimpleDateCondition(2010, 1, None).scanBack(self.startDate))
      self.assertEqual(len(dates), 10)

    def test_111_back_success(self):
      dates = list(SimpleDateCondition(2006, 5, 17).scanBack(self.startDate))
      self.assertEqual(dates, [datetime.date(2006, 5, 17)])
    def test_111_back_failure(self):
      dates = list(SimpleDateCondition(2012, 1, 11).scanBack(self.startDate))
      self.assertEqual(dates, [])


if __name__ == '__main__':
  unittest.main()
