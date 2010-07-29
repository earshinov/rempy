import datetime
import re
import time
import unittest


def dayOfYear(date):
  return (date - datetime.date(date.year, 1, 1)).days + 1

class _Test_dayOfYear(unittest.TestCase):

  def test_newYear(self):
    self.assertEqual(dayOfYear(datetime.date(2005, 1, 1)), 1)

  def test_basic(self):
    self.assertEqual(dayOfYear(datetime.date(2010, 12, 31)), 365)


def lastDayOfMonth(year, month):
  if month == 12:
    year = year+1
    month = 1
  else:
    month = month+1
  return datetime.date(year, month, 1) - datetime.timedelta(days=1)


def isoweekno(date):
  return date.isocalendar()[1]

class _Test_isoweekno(unittest.TestCase):

  def test_basic(self):
    self.assertEqual(isoweekno(datetime.date(2007, 12, 31)), 1)
    self.assertEqual(isoweekno(datetime.date(2008, 1, 1)), 1)
    self.assertEqual(isoweekno(datetime.date(2008, 1, 5)), 1)
    self.assertEqual(isoweekno(datetime.date(2008, 1, 9)), 2)

  def test_noThursday(self):
    self.assertEqual(isoweekno(datetime.date(2010, 1, 2)), 53)
    self.assertEqual(isoweekno(datetime.date(2010, 1, 5)), 1)


def weekno(date, startWeekday=0):
  begin = datetime.date(date.year, 1, 1)
  diff = (date - begin).days

  weekday = date.weekday()
  beginWeekday = (weekday - diff) % 7

  ret = diff / 7 + 1
  if weekday > beginWeekday:
    if startWeekday > beginWeekday and startWeekday <= weekday:
      ret += 1
  elif weekday < beginWeekday:
    if startWeekday > beginWeekday or startWeekday <= weekday:
      ret += 1
  return ret

class _Test_weekno(unittest.TestCase):

  def test_basic(self):
    self.assertEqual(weekno(datetime.date(2010, 1, 1)), 1)
    self.assertEqual(weekno(datetime.date(2010, 1, 3)), 1)
    self.assertEqual(weekno(datetime.date(2010, 1, 4)), 2)

  def test_yearStartsWithMonday(self):
    self.assertEqual(weekno(datetime.date(2007, 1, 1)), 1)
    self.assertEqual(weekno(datetime.date(2007, 1, 7)), 1)
    self.assertEqual(weekno(datetime.date(2007, 1, 8)), 2)

  def test_startWeekdayIsThursday(self):
    self.assertEqual(weekno(datetime.date(2008, 1, 1), 3), 1)
    self.assertEqual(weekno(datetime.date(2008, 1, 2), 3), 1)
    self.assertEqual(weekno(datetime.date(2008, 1, 3), 3), 2)
    self.assertEqual(weekno(datetime.date(2008, 1, 7), 3), 2)


class UnsafeDate(object):

  def __init__(self, year, month, day):
    super(UnsafeDate, self).__init__()
    self.year = year
    self.month = month
    self.day = day

  @staticmethod
  def fromDate(date):
    return UnsafeDate(date.year, date.month, date.day)

  def __cmp__(self, other):
    if self.year < other.year: return -1
    elif self.year > other.year: return 1
    if self.month < other.month: return -1
    elif self.month > other.month: return 1
    return self.day - other.day


class NonExistingDaysHandling:
  WRAP = 0
  SKIP = 1
  RAISE = 2

def wrapDate(unsafeDate, nonexistingDaysHandling=NonExistingDaysHandling.WRAP):
  try:
    return datetime.date(unsafeDate.year, unsafeDate.month, unsafeDate.day)
  except ValueError:
    case = nonexistingDaysHandling
    enum = NonExistingDaysHandling
    if case == enum.WRAP:
      return lastDayOfMonth(unsafeDate.year, unsafeDate.month)
    elif case == enum.SKIP:
      return None
    elif case == enum.RAISE:
      raise

# returns tuple (date, skip)
def wrapDate_noFail(unsafeDate, nonexistingDaysHandling):
  date = wrapDate(unsafeDate, nonexistingDaysHandling=NonExistingDaysHandling.WRAP)
  if date is None:
    return (lastDayOfMonth(unsafeDate.year, unsafeDate.month), True)
  else:
    return (date, False)


def parseIsoDate(string):
  return datetime.date(*(time.strptime(string, '%Y-%m-%d')[0:3]))
