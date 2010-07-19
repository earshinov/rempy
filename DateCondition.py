#!/usr/bin/env python

import bisect
import copy
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


# <http://docs.python.org/faq/programming.html#how-do-you-remove-duplicates-from-a-list>
def sortedUnique(mylist):
  if mylist == []:
    return
  last = mylist[-1]
  for i in xrange(len(mylist)-2, -1, -1):
    if last == mylist[i]:
      del mylist[i]
    else:
      last = mylist[i]


class DateCondition(object):

  def scan(self, startDate):
    return []

  def scanBack(self, startDate):
    return []


class NonExistingDaysHandling:
  WRAP = 0
  SKIP = 1
  RAISE = 2

class SimpleDateCondition(DateCondition):

  def __init__(self, year=None, month=None, day=None, weekdays=None,
      nonexistingDaysHandling=NonExistingDaysHandling.WRAP):
    super(SimpleDateCondition, self).__init__()
    self.year = year
    self.month = month
    self.day = day
    self.weekdays = weekdays
    if self.weekdays is not None:
      self.weekdays.sort()
      sortedUnique(self.weekdays)
    self.nonexistingDaysHandling = nonexistingDaysHandling

    # handle fixed date (for efficiency, see also __scan())
    self.theMatchingDay = None
    if self.day is not None and self.month is not None and self.year is not None:
      date = self.__wrapDate(self.UnsafeDate(self.year, self.month, self.day))
      if self.weekdays is None or date.weekday() in self.weekdays:
        self.theMatchingDay = date

    # "cache" for WeekdaysDayGeneratorHelper()
    if self.day is not None or self.weekdays is None or self.weekdays == []:
      self.weekdays_diff = None
    else:
      self.weekdays_diff = []
      for i in xrange(len(self.weekdays) - 1):
        increment = self.weekdays[i + 1] - self.weekdays[i]
        self.weekdays_diff.append(datetime.timedelta(days=increment))
      increment = self.weekdays[0] + 7 - self.weekdays[-1]
      self.weekdays_diff.append(datetime.timedelta(days=increment))

  def scan(self, startDate):
    return self.__scan(startDate)

  def scanBack(self, startDate):
    return self.__scan(startDate, back=True)


  def __scan(self, startDate, back=False):
    if self.weekdays == []:
      return []

    # handle fixed date (for efficiency, see also __init__())
    if self.day is not None and self.month is not None and self.year is not None:
      if self.theMatchingDay is None or \
          not back and startDate > self.theMatchingDay or \
          back and startDate < self.theMatchingDay:
        return []
      else:
        return [self.theMatchingDay]

    # handle the case when none of day, month, year is present
    if self.day is None and self.month is None and self.year is None:
      return self.__allDaysGenerator(startDate, back)

    unsafeDate = self.__findStartDate(startDate, back)
    if unsafeDate is None:
      return []

    daygen = self.__dayGenerator(unsafeDate, back) if self.day is None \
      else self.__fixedDayGenerator(unsafeDate)
    mongen = self.__monthGenerator(daygen, unsafeDate, back) if self.month is None \
      else self.__fixedMonthGenerator(daygen, unsafeDate)
    yeargen = self.__yearGenerator(mongen, unsafeDate, back) if self.year is None \
      else self.__fixedYearGenerator(mongen, unsafeDate)
    return yeargen

  def __findStartDate(self, startDate, back):
    op = operator.lt if not back else operator.gt
    delta = 1 if not back else -1

    month_start = 1 if not back else 12
    month_end = 12 if not back else 1

    class EmptyResult(Exception):
      pass

    def addYear(year):
      if self.year is None:
        return year + delta
      else:
        raise EmptyResult()

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
        return None

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

      return self.UnsafeDate(year, month, day)
    except EmptyResult:
      return None


  def __fixedYearGenerator(self, monthGenerator, unsafeDate):
    for _ in monthGenerator:
      if _ is None:
        return
      else:
        yield _

  def __yearGenerator(self, monthGenerator, unsafeDate, back):
    year = unsafeDate.year
    while True:
      for _ in monthGenerator:
        if _ is None:
          year += 1 if not back else -1
          monthGenerator.send(year)
        else:
          yield _

  def __fixedMonthGenerator(self, dayGenerator, unsafeDate):
    month = unsafeDate.month
    for _ in dayGenerator:
      if _ is None:
        year = (yield _); yield None
        assert year is not None
        dayGenerator.send((year, month))
      else:
        yield _

  def __monthGenerator(self, dayGenerator, unsafeDate, back):
    delta = 1 if not back else -1
    month_start = 1 if not back else 12
    month_end = 12 if not back else 1

    year, month = (unsafeDate.year, unsafeDate.month)
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

  def __fixedDayGenerator(self, unsafeDate_):
    unsafeDate = copy.copy(unsafeDate_)
    while True:
      date = self.__wrapDate(unsafeDate)
      if date is not None:
        if self.weekdays is None or date.weekday() in self.weekdays:
          yield date
      (unsafeDate.year, unsafeDate.month) = (yield None); yield None


  class DayGeneratorHelper(object):
    initiallyCheckWeekday = False

    @staticmethod
    def new(cond, back):
      if cond.weekdays is not None:
        return SimpleDateCondition.WeekdaysDayGeneratorHelper(cond, back)
      else:
        return SimpleDateCondition.SimpleDayGeneratorHelper(back)

    def checkWeekday(self, date):
      raise NotImplementedError()

    def step(self, date):
      raise NotImplementedError()

  class SimpleDayGeneratorHelper(DayGeneratorHelper):

    def __init__(self, back):
      super(SimpleDateCondition.SimpleDayGeneratorHelper, self).__init__()
      self.timedelta = datetime.timedelta(days=1 if not back else -1)

    def checkWeekday(self, date):
      return date

    def step(self, date):
      return date + self.timedelta

  class WeekdaysDayGeneratorHelper(DayGeneratorHelper):
    initiallyCheckWeekday = True

    def __init__(self, cond, back):
      super(SimpleDateCondition.WeekdaysDayGeneratorHelper, self).__init__()
      self.cond = cond
      self.back = back
      self.weekdays_diff_index = None

    def checkWeekday(self, date):
      # this fails when self.cond.weekdays == []
      # the condition is checked in __scan()
      date_weekday = date.weekday()
      if not self.back:
        i = bisect.bisect_left(self.cond.weekdays, date_weekday)
        increment = 7 if (i == len(self.cond.weekdays)) else 0
        i = i % len(self.cond.weekdays)
      else:
        i = bisect.bisect_right(self.cond.weekdays, date_weekday)
        increment = -7 if (i == 0) else 0
        i = (i-1) % len(self.cond.weekdays)
      increment += self.cond.weekdays[i] - date_weekday

      self.weekdays_diff_index = i if not self.back \
        else (i-1) % len(self.cond.weekdays)
      return date + datetime.timedelta(days=increment)

    def step(self, date):
      timedelta = self.cond.weekdays_diff[self.weekdays_diff_index]
      self.weekdays_diff_index += 1 if not self.back else -1
      self.weekdays_diff_index %= len(self.cond.weekdays_diff)
      return date + timedelta if not self.back else date - timedelta

  def __dayGenerator(self, unsafeDate, back):
    helper = self.DayGeneratorHelper.new(self, back)

    first = True
    while True:
      if first:
        date, skip = self.__wrapDate_noFail(unsafeDate)
        if helper.initiallyCheckWeekday:
          nextDate = helper.checkWeekday(date)
          if date == nextDate and skip:
            nextDate = helper.step(nextDate)
        else:
          if not skip: yield date
          nextDate = helper.step(date)
        first = False
      else:
        yield date
        nextDate = helper.step(date)

      while date != nextDate:
        if date.month != nextDate.month:
          (year, month) = (yield None); yield None
          if year != nextDate.year or month != nextDate.month:
            date = datetime.date(year, month, 1) if not back \
              else lastDayOfMonth(year, month)
            nextDate = helper.checkWeekday(date)
            continue
        date = nextDate

  def __allDaysGenerator(self, date, back):
    helper = self.DayGeneratorHelper.new(self, back)
    if helper.initiallyCheckWeekday:
      date = helper.checkWeekday(date)
    while True:
      yield date
      date = helper.step(date)


  class UnsafeDate(object):

    def __init__(self, year, month, day):
      super(SimpleDateCondition.UnsafeDate, self).__init__()
      self.year = year
      self.month = month
      self.day = day

  def __wrapDate(self, unsafeDate):
    try:
      return datetime.date(unsafeDate.year, unsafeDate.month, unsafeDate.day)
    except ValueError:
      case = self.nonexistingDaysHandling
      enum = NonExistingDaysHandling
      if case == enum.WRAP:
        return lastDayOfMonth(unsafeDate.year, unsafeDate.month)
      elif case == enum.SKIP:
        return None
      elif case == enum.RAISE:
        raise

  # returns tuple (date, skip)
  def __wrapDate_noFail(self, unsafeDate):
    date = self.__wrapDate(unsafeDate)
    if date is None:
      return (lastDayOfMonth(unsafeDate.year, unsafeDate.month), True)
    else:
      return (date, False)


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

    # Special: handling of non-existing days

    def test_nonexisting_wrap(self):
      dates = list(self.__nonexistingDays(NonExistingDaysHandling.WRAP))
      self.assertEqual(len(dates), 12)
      self.assertEqual(dates[1], datetime.date(2010, 2, 28))
    def test_nonexisting_skip(self):
      gen = self.__nonexistingDays(NonExistingDaysHandling.SKIP);
      months = list(date.month for date in gen)
      self.assertEquals(months, [1,3,5,7,8,10,12])
    def test_nonexisting_raise(self):
      self.assertRaises(ValueError, lambda: \
        list(self.__nonexistingDays(NonExistingDaysHandling.RAISE)))

    def __nonexistingDays(self, nonexistingDaysHandling):
      cond = SimpleDateCondition(2010, None, 31,
        nonexistingDaysHandling=nonexistingDaysHandling)
      for date in cond.scan(self.startDate): yield date

    def test_nonexisting_start_wrap(self):
      cond = SimpleDateCondition(None, 2, 29)
      dates = list(itertools.islice(cond.scan(self.startDate), 4))
      self.assertEqual(dates, [
        datetime.date(2010, 2, 28),
        datetime.date(2011, 2, 28),
        datetime.date(2012, 2, 29),
        datetime.date(2013, 2, 28),
      ])
    def test_nonexisting_start_skip(self):
      cond = SimpleDateCondition(None, 2, 29,
        nonexistingDaysHandling=NonExistingDaysHandling.SKIP)
      dates = list(itertools.islice(cond.scan(self.startDate), 2))
      self.assertEqual(dates, [
        datetime.date(2012, 2, 29),
        datetime.date(2016, 2, 29),
      ])
    def test_nonexisting_start_weekday(self):
      cond = SimpleDateCondition(None, 2, 29, weekdays=[6],
        nonexistingDaysHandling=NonExistingDaysHandling.SKIP)
      dates = list(itertools.islice(cond.scan(self.startDate), 2))
      self.assertEqual(dates, [
        datetime.date(2032, 2, 29),
        datetime.date(2060, 2, 29),
      ])

    # Special: week days

    def test_weekdays_empty(self):
      dates = list(SimpleDateCondition(None, None, None, weekdays=[]).scan(self.startDate))
      self.assertEqual(dates, [])

    def test_weekdays(self):
      cond = SimpleDateCondition(None, None, None, weekdays=[2,6,0])
      dates = list(itertools.islice(cond.scan(datetime.date(2009, 12, 25)), 5))
      self.assertEqual(dates, [
        datetime.date(2009, 12, 27),
        datetime.date(2009, 12, 28),
        datetime.date(2009, 12, 30),
        datetime.date(2010, 01, 3),
        datetime.date(2010, 01, 4),
      ])
    def test_weekdays_startDayMatch(self):
      cond = SimpleDateCondition(2010, 1, None, weekdays=[5,6])
      dates = list(itertools.islice(cond.scan(self.startDate), 1))
      self.assertEqual(dates, [self.startDate])

    def test_weekdays_back(self):
      cond = SimpleDateCondition(None, None, None, weekdays=[0,1])
      dates = list(itertools.islice(cond.scanBack(self.startDate), 5))
      self.assertEqual(dates, [
        datetime.date(2010, 1, 5),
        datetime.date(2010, 1, 4),
        datetime.date(2009, 12, 29),
        datetime.date(2009, 12, 28),
        datetime.date(2009, 12, 22),
      ])
    def test_weekdays_back_startDayMatch(self):
      cond = SimpleDateCondition(None, 1, None, weekdays=[1,6])
      dates = list(itertools.islice(cond.scanBack(self.startDate), 1))
      self.assertEqual(dates, [self.startDate])

    def test_weekdays_fixedMonth(self):
      cond = SimpleDateCondition(None, 1, None, weekdays=[3])
      dates = list(itertools.islice(cond.scan(self.startDate), 5))
      self.assertEqual(dates, [
        datetime.date(2010, 1, 14),
        datetime.date(2010, 1, 21),
        datetime.date(2010, 1, 28),
        datetime.date(2011, 1, 6),
        datetime.date(2011, 1, 13),
      ])

    # Special: fixed dates

    def test_fixed_weekdays_success(self):
      dates = SimpleDateCondition(2010, 9, 1, weekdays=[0,2,6]).scan(self.startDate)
      self.assertEqual(dates, [datetime.date(2010, 9, 1)])
    def test_fixed_weekdays_failure(self):
      dates = SimpleDateCondition(2010, 9, 1, weekdays=[1,3]).scan(self.startDate)
      self.assertEqual(dates, [])


class RepeatDateCondition(DateCondition):

  def __init__(self, period):
    super(RepeatDateCondition, self).__init__()
    self.timedelta = datetime.timedelta(days=period)

  def scan(self, startDate):
    date = startDate
    while True:
      yield date
      date = date + self.timedelta

  def scanBack(self, startDate):
    date = startDate
    while True:
      yield date
      date = date - self.timedelta


  class Test(unittest.TestCase):

    def setUp(self):
      self.startDate = datetime.date(2010, 7, 16)

    def test_basic(self):
      cond = RepeatDateCondition(30)
      dates = list(itertools.islice(cond.scan(self.startDate), 2))
      self.assertEqual(dates, [
        datetime.date(2010, 7, 16),
        datetime.date(2010, 8, 15),
      ])


class ShiftDateCondition(DateCondition):

  def __init__(self, shift):
    super(ShiftDateCondition, self).__init__()
    self.timedelta = datetime.timedelta(days=shift)

  def scan(self, startDate):
    yield startDate + self.timedelta

  def scanBack(self, startDate):
    yield startDate + self.timedelta


class SatisfyDateCondition(DateCondition):

  # dateCondition can be None
  def __init__(self, cond, satisfy):
    super(SatisfyDateCondition, self).__init__()
    self.cond = cond
    self.satisfy = satisfy

  def scan(self, startDate):
    return self.__scan(startDate)

  def scanBack(self, startDate):
    return self.__scan(startDate, back=True)

  def __scan(self, startDate, back=False):
    if self.cond is None:
      date = startDate
      timedelta = datetime.timedelta(days=1 if not back else -1)
      while True:
        if self.satisfy(date):
          yield date
        date = date + timedelta
    else:
      gen = self.cond.scan(startDate) if not back else self.cond.scanBack(startDate)
      for date in gen:
        if self.satisfy(date):
          yield date


  class Test(unittest.TestCase):

    def setUp(self):
      self.startDate = datetime.date(2010, 7, 16)

    def test_basic(self):
      everyMonday = SimpleDateCondition(2010, None, None, weekdays=[0])
      everySecondMonday = SatisfyDateCondition(everyMonday, self.__Odd())
      gen = everySecondMonday.scan(datetime.date(2010, 1, 1))
      the2ndMonday = gen.next()
      self.assertEqual(the2ndMonday, datetime.date(2010, 1, 11))
      the20thMonday = next(itertools.islice(gen, 8, None))
      self.assertEqual(the20thMonday, datetime.date(2010, 5, 17))

    def test_none(self):
      everySecondDay = SatisfyDateCondition(None, self.__Odd())
      gen = everySecondDay.scanBack(datetime.date(2009, 12, 31))
      the6thDayBack = next(itertools.islice(gen, 2, None))
      self.assertEqual(the6thDayBack, datetime.date(2009, 12, 26))

    class __Odd(object):

      def __init__(self):
        object.__init__(self)
        self.switch = 0

      def __call__(self, date):
        self.switch = 1 - self.switch
        return self.switch == 0


class LimitedDateCondition(DateCondition):

  def __init__(self, cond, from_=None, until=None, maxMatches=None):
    super(LimitedDateCondition, self).__init__()
    self.cond = cond
    self.from_ = from_
    self.until = until
    self.maxMatches = maxMatches

  def scan(self, startDate):
    if self.from_ is not None:
      startDate = max(startDate, self.from_)
    gen = self.cond.scan(startDate)
    if self.until is not None:
      gen = itertools.takewhile(lambda date: date <= self.until, gen)
    if self.maxMatches is not None:
      gen = itertools.islice(gen, self.maxMatches)
    return gen

  def scanBack(self, startDate):
    if self.until is not None:
      startDate = min(startDate, self.until)
    gen = self.cond.scanBack(startDate)
    if self.from_ is not None:
      gen = itertools.takewhile(lambda date: date <= self.until, gen)
    if self.maxMatches is not None:
      gen = itertools.islice(gen, self.maxMatches)
    return gen


class CombinedDateCondition(DateCondition):

  def __init__(self, cond, cond2, scanBack=False):
    super(CombinedDateCondition, self).__init__()
    self.cond = cond
    self.cond2 = cond2
    self.back = scanBack

  def scan(self, startDate):
    for date in self.cond.scan(startDate):
      for date2 in self.__applyCond2(date):
        yield date2

  def scanBack(self, startDate):
    for date in self.cond.scanBack(startDate):
      for date2 in self.__applyCond2(date):
        yield date2

  def __applyCond2(self, date):
    gen = self.cond2.scan(date) if not self.back \
      else self.cond2.scanBack(date)
    for date2 in gen:
      yield date2


  class Test(unittest.TestCase):

    def setUp(self):
      self.startDate = datetime.date(2010, 3, 31)

    def test_lastWeekday(self):
      cond = CombinedDateCondition(
        SimpleDateCondition(None, 4, 30),
        LimitedDateCondition(
          SimpleDateCondition(None, None, None, weekdays=[0]),
          maxMatches = 1),
        scanBack=True)
      lastAprilMondays = list(itertools.islice(cond.scan(self.startDate), 2))
      self.assertEqual(lastAprilMondays, [
        datetime.date(2010, 4, 26),
        datetime.date(2011, 4, 25),
      ])


if __name__ == '__main__':
  unittest.main()
