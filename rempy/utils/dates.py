# -*- coding: utf-8 -*-

'''Функции и классы для работы с датами'''

import datetime
import re
import time
import unittest


def dayOfYear(date):
  '''Получить порядковый номер дня в году

  @param date: объект класса C{datetime.date}
  @returns: порядковый номер дня в году как целое число (считается с 1)
  '''
  return (date - datetime.date(date.year, 1, 1)).days + 1

class _Test_dayOfYear(unittest.TestCase):
  '''Набор unit-тестов для функции L{dayOfYear}'''

  def test_newYear(self):
    self.assertEqual(dayOfYear(datetime.date(2005, 1, 1)), 1)

  def test_basic(self):
    self.assertEqual(dayOfYear(datetime.date(2010, 12, 31)), 365)


def lastDayOfMonth(year, month):
  '''Получить последний день месяца

  @param year: целочисленное значение, номер года
  @param month: целочисленное значение, номер месяца (1-12)
  @returns: объект класса C{datetime.date}
  '''
  if month == 12:
    year = year+1
    month = 1
  else:
    month = month+1
  return datetime.date(year, month, 1) - datetime.timedelta(days=1)


def isoweekno(date):
  '''Получить номер недели согласно стандарту ISO

  @param date: объект класса C{datetime.date}
  @returns: номер недели как целое число
  '''
  return date.isocalendar()[1]

class _Test_isoweekno(unittest.TestCase):
  '''Набор unit-тестов для функции L{isoweekno}'''

  def test_basic(self):
    self.assertEqual(isoweekno(datetime.date(2007, 12, 31)), 1)
    self.assertEqual(isoweekno(datetime.date(2008, 1, 1)), 1)
    self.assertEqual(isoweekno(datetime.date(2008, 1, 5)), 1)
    self.assertEqual(isoweekno(datetime.date(2008, 1, 9)), 2)

  def test_noThursday(self):
    self.assertEqual(isoweekno(datetime.date(2010, 1, 2)), 53)
    self.assertEqual(isoweekno(datetime.date(2010, 1, 5)), 1)


def weekno(date, startWeekday=0):
  '''Получить номер недели согласно традиционным представлениям: первый день
  включается в первую неделю

  @param date: объект класса C{datetime.date}
  @param startWeekday: начальный день недели (0 - понедельник, 6 - воскресенье)
  '''
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
  '''Набор unit-тестов для функции L{weekno}'''

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
  '''Класс, который хранит год, месяц и день, но не проверяет, составляют ли
  они существующую дату

  @ivar year: полный номер года
  @ivar month: месяц (1-12)
  @ivar day: день (1-31)
  '''

  def __init__(self, year, month, day):
    super(UnsafeDate, self).__init__()
    self.year = year
    self.month = month
    self.day = day

  @staticmethod
  def fromDate(date):
    '''Сконструировать объект класса L{UnsafeDate}, хранящий ту же дату,
    что и заданный объект класса C{datetime.date}

    @param date: объект класса C{datetime.date}
    @returns: объект класса L{UnsafeDate}
    '''
    return UnsafeDate(date.year, date.month, date.day)

  def __cmp__(self, other):
    if self.year < other.year: return -1
    elif self.year > other.year: return 1
    if self.month < other.month: return -1
    elif self.month > other.month: return 1
    return self.day - other.day


class NonExistingDaysHandling:
  '''Способы обработки несуществующих дат'''

  WRAP = 0
  '''Выбрать последний день месяца'''

  SKIP = 1
  '''Пропустить, что бы это ни значило в конкретном контексте'''

  RAISE = 2
  '''Выбросить C{ValueError}'''

def wrapDate(unsafeDate, nonexistingDaysHandling=NonExistingDaysHandling.WRAP):
  '''Преобразовать объект класса L{UnsafeDate} в объект класса C{datetime.date}.

  @param unsafeDate: объект класса L{UnsafeDate}
  @param nonexistingDaysHandling: элемент «перечисления»
    L{NonExistingDaysHandling}, задающий способ обработки ситуации, когда
    C{unsafeDate} содержит несуществующую дату:

      - если C{WRAP}, будет возвращён последний день месяца
      - если C{SKIP}, будет возвращено значение C{None}
      - если C{RAISE}, будет выброшено исключение C{ValueError}

  @returns: объект класса C{datetime.date} или, если C{unsafeDate} содержит
    несуществующую дату, в завимости от значения C{nonexistingDaysHandling}
  '''
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
  '''Преобразовать объект класса L{UnsafeDate} в объект класса C{datetime.date}.

  @param unsafeDate: объект класса L{UnsafeDate}
  @param nonexistingDaysHandling: элемент «перечисления»
    L{NonExistingDaysHandling}, задающий способ обработки ситуации, когда
    C{unsafeDate} содержит несуществующую дату.  В случае C{WRAP} или C{SKIP}
    первым элементов возвращаемого кортежа будет последний день месяца, вторым -
    C{False} в случае C{WRAP}, C{True} в случае C{SKIP}.
  @returns: кортеж из двух элементов

    - объект класса C{datetime.date}
    - логическое значение, равное C{True}, если эту дату следует «пропусить»
  '''
  date = wrapDate(unsafeDate, nonexistingDaysHandling=NonExistingDaysHandling.WRAP)
  if date is None:
    return (lastDayOfMonth(unsafeDate.year, unsafeDate.month), True)
  else:
    return (date, False)


def parseIsoDate(string):
  '''Разобрать строку даты в формате ISO

  @param string: строка вида YYYY-mm-dd
  @returns: объект класса C{datetime.date}
  @raise C{ValueError}: строка имеет неправильный формат
  '''
  return datetime.date(*(time.strptime(string, '%Y-%m-%d')[0:3]))
