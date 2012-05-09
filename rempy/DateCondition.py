# -*- coding: utf-8 -*-

'''Содержит иерархию классов L{DateCondition}

При запуске из командной строки запускает присутствующие в модуле unit-тесты.'''

import bisect
import copy
import datetime
import itertools
import operator
import unittest

from utils import FormatError
from utils.algorithms import sortedUnique
from utils.dates import UnsafeDate, NonExistingDaysHandling
from utils.functional import all
import utils.dates as dateutils


class DateCondition(object):
  '''Базовый класс для классов, которые могут хранить условия на дату и
  находить даты, удовлетворяющие этим условиям.'''

  def scan(self, startDate):
    '''Искать даты, удовлетворяющие хранимым в объекте условиям, в направлении
    будущего, начиная со L{startDate} включительно.

    Метод предназначен для переопределения в наследниках.  При этом
    возвращаемый генератором поток дат должен обладать следующими свойствами:

      - никакая из дат не должна быть меньше C{startDate};
      - поток должен быть строго упорядоченным (каждая следующая дата
        должна быть строго больше предыдущей).

    @param startDate: объект класса C{datetime.date},
      задающий начальную дату для поиска
    @returns: Iterable по датам (объектам класса C{datetime.date})
    '''
    return []

  def scanBack(self, startDate):
    '''Искать даты, удовлетворяющие хранимым в объекте условиям, в направлении
    прошлого, начиная со L{startDate} включительно.

    Сам по себе поиск дат в прошлом навряд ли нужен конечному пользователю,
    но такая возможность может пригодиться при написании собственных классов
    условий, в которых используется композиция.  В качестве примера см.
    L{DeferrableDateCondition<contrib.deferrable.DateCondition.DeferrableDateCondition>}.

    Метод предназначен для переопределения в наследниках.  При этом
    возвращаемый генератором поток дат должен обладать следующими свойствами:

      - никакая из дат не должна быть больше C{startDate};
      - поток должен быть строго упорядоченным (каждая следующая дата
        должна быть строго меньше предыдущей).

    @param startDate: объект класса C{datetime.date},
      задающий начальную дату для поиска
    @returns: Iterable по датам (объектам класса C{datetime.date})
    '''
    return []

  @staticmethod
  def fromString(string):
    '''Удобная функция для конструирования объекта класса L{DateCondition} по
    строке формата, похожего на формат описания напоминалок в программе remind.

    @param string: Строка заданного формата.  Более подробно о формате см. в
      документации класса L{DateConditionParser<StringParser.DateConditionParser>}.
    @returns: объект класса L{DateCondition}
    @raise FormatError: в случае ошибки разбора строки
    '''
    return DateConditionParser().parse(string)


class SimpleDateCondition(DateCondition):
  '''Класс, позволяющий находить даты по номеру дня в месяце, месяцу, году,
  дням недели.  Любой из этих параметров может быть опущен.

  Обработка дней недели отличается от оной в Remind.  Используемая здесь
  стратегия более проста и логична, но менее полезна конечным пользователям.
  Суть стратегии в том, что указание дней недели означает то и только то,
  что из дат, соответствующих другим условиям (год, месяц, день), выбираются
  даты с одним из перечисленных дней недели.
  '''

  def __init__(self, year=None, month=None, day=None, weekdays=None,
      nonexistingDaysHandling=dateutils.NonExistingDaysHandling.WRAP):
    '''Конструктор.

    @param year: Целочисленное значение, задающее номер года.  Если
      передано C{None}, ограничение на год подходящей даты не накладывается.
    @param month: Целочисленное значение в интервале [1..12], задающее месяц.
      Если передано C{None}, ограничение на месяц подходящей даты не накладывается.
    @param day: Целочисленное значение, задающее номер дня в месяцу.  Если
      передано C{None}, ограничение на номер дня не накладывается.
    @param weekdays: Коллекция целочисленных значений, каждое из которых
      задаёт день недели.  Дни недели кодируются числами от 0 (понедельник)
      до 6 (воскресенье).  Если передано C{None}, ограничение на день недели
      подходящей даты не накладывается.

    @param nonexistingDaysHandling:  Второстепенный параметр класса
      L{utils.dates.NonExistingDaysHandling}, влияющий на то,
      как обрабатываются несуществующие даты.  Имеют смысл значения
      L{WRAP<utils.dates.NonExistingDaysHandling.WRAP>} (умолчание) и
      L{SKIP<utils.dates.NonExistingDaysHandling.SKIP>}.  Как они работают,
      проще всего продемострировать на примере.  Если у нас есть
      C{SimpleDateCondition(day=31)}, то в первом случае в результат методов
      L{scan} и L{scanBack} для каждого года будет включён последний день
      февраля; во втором случае дни из февраля в результат не попадут.
    '''
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
      date = self.__wrapDate(dateutils.UnsafeDate(self.year, self.month, self.day))
      if self.weekdays is None or date.weekday() in self.weekdays:
        self.theMatchingDay = date

    # "cache" for _WeekdaysDayGeneratorHelper
    if self.day is not None or self.weekdays is None or self.weekdays == []:
      self.weekdays_diff = None
    else:
      self.weekdays_diff = []
      for i in xrange(len(self.weekdays) - 1):
        increment = self.weekdays[i + 1] - self.weekdays[i]
        self.weekdays_diff.append(datetime.timedelta(days=increment))
      increment = self.weekdays[0] + 7 - self.weekdays[-1]
      self.weekdays_diff.append(datetime.timedelta(days=increment))


  def __wrapDate(self, unsafeDate):
    return dateutils.wrapDate(unsafeDate, self.nonexistingDaysHandling)

  def __wrapDate_noFail(self, unsafeDate):
    return dateutils.wrapDate_noFail(unsafeDate, self.nonexistingDaysHandling)


  def scan(self, startDate):
    return self.__scan(startDate)

  def scanBack(self, startDate):
    return self.__scan(startDate, back=True)


  def __scan(self, startDate, back=False):
    '''Общая реализация открытых методов L{scan} и L{scanBack}.

    Для нахождения первой подходящей даты используется метод L{__findStartDate}.
    Далее подходящие даты перебираются с использованием трёх генераторов, по
    одному для года, месяца и дня.  Генераторы объединяются в цепочку: даты,
    возвращаемые генератором дней, передаются генератору месяцев и т.д.  Даты,
    возвращаемые генератором лет, возвращаются из метода.

    Генератор обращается к вышестоящему каждый раз, когда ему надо начать
    очередной цикл перебора дат.  К примеру, генератор дней, используемый
    внутри объекта C{SimpleDateCondition(month=5)}, периодически выводит дни до
    окончания месяца и обращается к генератору месяцев для продолжения.

    Обращение к вышестоящему генератору реализуется через возвращение C{None} в
    качестве очередной даты и получение ответа с использованием
    U{yield expression<http://docs.python.org/reference/expressions.html#yieldexpr>}.
    Генератор лет в качестве ответа возвращает номер очередного года,
    генератор месяцев -- набор (номер года, номер месяца).

    @param startDate: начальная дата для поиска подходящих дат
    @param back: C{False} в случае вызова из L{scan} (сканирования в
      направлении будущего), C{True} в случае вызова из L{scanBack}
      (сканирования в направлении прошлого).
    @returns: результат для методов L{scan} и L{scanBack} (Iterable по объектам
      класса C{datetime.date}).
    '''
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
    '''Найти первую дату, удовлетворяющую условиям.

    @param startDate: объект класса C{datetime.date},
      задающий начальную дату для поиска
    @param back: если C{True}, поиск ведётся в направлении прошлого,
      иначе в направлении будущего
    @returns: объект класса L{UnsafeDate<utils.dates.UnsafeDate>} или C{None},
      если подходящих дат не найдено
    '''
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
          day = 1 if not back else dateutils.lastDayOfMonth(year, month).day
      elif op(day, startDate.day) and atStartDate:
        (year, month) = addMonth(year, month)

      return dateutils.UnsafeDate(year, month, day)
    except EmptyResult:
      return None


  def __fixedYearGenerator(self, monthGenerator, unsafeDate):
    '''Генератор лет, используемый, если в условии задан фиксированный год.

    @param monthGenerator: генератор месяцев
    @param unsafeDate: объект класса L{Unsafedate<utils.dates.UnsafeDate>},
      задающий начальную дату
    @returns: Iterable по датам (объектам класса C{datetime.date}).  Для
      взаимодействия с вышестоящим генератором Iterable может также
      возвращать C{None}.
    @see: L{__scan}
    '''
    for _ in monthGenerator:
      if _ is None:
        return
      else:
        yield _

  def __yearGenerator(self, monthGenerator, unsafeDate, back):
    '''Генератор лет, используемый, если год не фиксирован.

    @param monthGenerator: генератор месяцев
    @param unsafeDate: объект класса L{Unsafedate<utils.dates.UnsafeDate>},
      задающий начальную дату
    @param back: если C{True}, поиск ведётся в направлении прошлого,
      иначе в направлении будущего
    @returns: Iterable по датам (объектам класса C{datetime.date}).  Для
      взаимодействия с вышестоящим генератором Iterable может также
      возвращать C{None}.
    @see: L{__scan}
    '''
    year = unsafeDate.year
    while True:
      for _ in monthGenerator:
        if _ is None:
          year += 1 if not back else -1
          monthGenerator.send(year)
        else:
          yield _

  def __fixedMonthGenerator(self, dayGenerator, unsafeDate):
    '''Генератор месяцев, используемый, если в условии задан фиксированный месяц.

    @param dayGenerator: генератор дней
    @param unsafeDate: объект класса L{Unsafedate<utils.dates.UnsafeDate>},
      задающий начальную дату
    @returns: Iterable по датам (объектам класса C{datetime.date}).  Для
      взаимодействия с вышестоящим генератором Iterable может также
      возвращать C{None}.
    @see: L{__scan}
    '''
    month = unsafeDate.month
    for _ in dayGenerator:
      if _ is None:
        year = (yield _); yield None
        assert year is not None
        dayGenerator.send((year, month))
      else:
        yield _

  def __monthGenerator(self, dayGenerator, unsafeDate, back):
    '''Генератор лет, используемый, если месяц не фиксирован.

    @param dayGenerator: генератор дней
    @param unsafeDate: объект класса L{Unsafedate<utils.dates.UnsafeDate>},
      задающий начальную дату
    @param back: если C{True}, поиск ведётся в направлении прошлого,
      иначе в направлении будущего
    @returns: Iterable по датам (объектам класса :std:`datetime.date`).  Для
      взаимодействия с вышестоящим генератором Iterable может также
      возвращать C{None}.
    @see: L{__scan}
    '''
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
    '''Генератор дней, используемый, если в условии задан фиксированный номер дня.

    @param unsafeDate_: объект класса L{Unsafedate<utils.dates.UnsafeDate>},
      задающий начальную дату
    @returns: Iterable по датам (объектам класса C{datetime.date}).  Для
      взаимодействия с вышестоящим генератором Iterable может также
      возвращать C{None}.
    @see: L{__scan}
    '''
    unsafeDate = copy.copy(unsafeDate_)
    while True:
      date = self.__wrapDate(unsafeDate)
      if date is not None:
        if self.weekdays is None or date.weekday() in self.weekdays:
          yield date
      (unsafeDate.year, unsafeDate.month) = (yield None); yield None


  class _DayGeneratorHelper(object):
    '''Базовый класс для вспомогательных классов, которые используются в
    генераторах дней для того, чтобы в случае, если в условии задан список
    дней недели, сократить перебор дат, рассматривая только те, которые
    попадают в этот список.'''

    def __init__(self):
      super(SimpleDateCondition._DayGeneratorHelper, self).__init__()
      self.lastDate = None

    @staticmethod
    def new(cond, back):
      '''Основной способ конструирования объектов этого класса.  Создаёт
      объект конкретного дочернего класса в зависимости от того, задан ли
      список дней недели в условии.'''
      if cond.weekdays is not None:
        return SimpleDateCondition._WeekdaysDayGeneratorHelper(cond, back)
      else:
        return SimpleDateCondition._SimpleDayGeneratorHelper(back)

    def checkWeekday(self, date):
      '''Найти дату ≥ C{date}, подходящую по дню недели.  Делегирует работу
      методу L{_checkWeekday}, который реализуется в наследниках.

      @param date: объект класса C{datetime.date}
      @returns: объект класса C{datetime.date}
      '''
      self.lastDate = self._checkWeekday(date)
      return self.lastDate

    def _checkWeekday(self, date):
      '''Метод для определения в наследниках.  Реализация метода L{checkWeekday}

      @param date: объект класса C{datetime.date}
      @returns: объект класса C{datetime.date}

      @see: L{checkWeekday}
      '''
      raise NotImplementedError()

    def step(self):
      '''Найти дату, следующую за предыдущей датой, возвращённой этим методом
      или методом L{checkWeekday}.  Делегирует работу методу L{_step}, который
      реализуется в наследниках.

      @returns: объект класса C{datetime.date}
      '''
      self.lastDate = self._step(self.lastDate)
      return self.lastDate

    def _step(self, date):
      '''Метод для определения в наследниках.  Реализация метода L{step}

      @param date: последняя дата, возвращённая этим методом или методом L{_checkWeekday}
      @returns: объект класса C{datetime.date}

      @see: L{step}
      '''
      raise NotImplementedError()

  class _SimpleDayGeneratorHelper(_DayGeneratorHelper):
    '''Вспомогательный класс для генераторов дней, который используется
    в случае, когда нет ограничений на день недели.

    @see: L{_DayGeneratorHelper}
    '''

    def __init__(self, back):
      '''Конструктор

      @param back: если C{True}, поиск ведётся в направлении прошлого,
        иначе в направлении будущего
      '''
      super(SimpleDateCondition._SimpleDayGeneratorHelper, self).__init__()
      self.timedelta = datetime.timedelta(days=1 if not back else -1)

    def _checkWeekday(self, date):
      return date

    def _step(self, date):
      return date + self.timedelta

  class _WeekdaysDayGeneratorHelper(_DayGeneratorHelper):
    '''Вспомогательный кдасс для генераторов дней, который используется
    в случае, когда в условии есть ограничения на день недели.

    Получает в конструктор объект класса L{SimpleDateCondition} и использует
    его атрибуты L{weekdays<SimpleDateCondition.weekdays>} и
    L{weekdays_diff<SimpleDateCondition.weekdays_diff>}.

    @see: L{_DayGeneratorHelper}
    '''

    def __init__(self, cond, back):
      '''Конструктор

      @param cond: объект класса L{SimpleDateCondition}
      @param back: если C{True}, поиск ведётся в направлении прошлого,
        иначе в направлении будущего
      '''
      super(SimpleDateCondition._WeekdaysDayGeneratorHelper, self).__init__()
      self.cond = cond
      self.back = back
      self.weekdays_diff_index = None

    def _checkWeekday(self, date):
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

    def _step(self, date):
      timedelta = self.cond.weekdays_diff[self.weekdays_diff_index]
      self.weekdays_diff_index += 1 if not self.back else -1
      self.weekdays_diff_index %= len(self.cond.weekdays_diff)
      return date + timedelta if not self.back else date - timedelta

  def __dayGenerator(self, unsafeDate, back):
    '''Генератор дней, используемый, если номер дня не фиксирован.

    @param unsafeDate: объект класса L{Unsafedate<utils.dates.UnsafeDate>},
      задающий начальную дату
    @param back: если C{True}, поиск ведётся в направлении прошлого,
      иначе в направлении будущего
    @returns: Iterable по датам (объектам класса C{datetime.date}).  Для
      взаимодействия с вышестоящим генератором Iterable может также
      возвращать C{None}.
    @see: L{__scan}
    '''
    helper = self._DayGeneratorHelper.new(self, back)

    date, skip = self.__wrapDate_noFail(unsafeDate)
    nextDate = helper.checkWeekday(date)
    if date == nextDate and skip:
      nextDate = helper.step()

    while True:

      # Find a date satisfying both weekday and year-month-day conditions
      while date != nextDate:
        if date.month != nextDate.month:
          (year, month) = (yield None); yield None
          if year != nextDate.year or month != nextDate.month:
            date = datetime.date(year, month, 1) if not back \
              else dateutils.lastDayOfMonth(year, month)
            nextDate = helper.checkWeekday(date)
            continue
        date = nextDate

      yield date
      nextDate = helper.step()

  def __allDaysGenerator(self, date, back):
    '''Простой генератор, используемый, когда не задан
    ни один из компонентов даты.

    @param date: объект класса C{datetime.date}, задающий начальную дату
    @param back: если C{True}, поиск ведётся в направлении прошлого,
      иначе в направлении будущего
    @returns: Iterable по датам (объектам класса C{datetime.date})
    @see: L{__scan}
    '''
    helper = self._DayGeneratorHelper.new(self, back)
    yield helper.checkWeekday(date)
    while True:
      yield helper.step()


  class Test(unittest.TestCase):
    '''Набор unit-тестов'''

    def setUp(self):
      self.startDate = datetime.date(2010, 1, 10)

    # Basic: forward scanning

    def test_000(self):
      gen = SimpleDateCondition(None, None, None).scan(self.startDate)
      date = itertools.islice(gen, 365*2, None).next()
      self.assertEqual(date, datetime.date(2012, 1, 10))

    def test_001(self):
      gen = SimpleDateCondition(None, None, 17).scan(self.startDate)
      date = itertools.islice(gen, 13, None).next()
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
      dates = list(self.__nonexistingDays(dateutils.NonExistingDaysHandling.WRAP))
      self.assertEqual(len(dates), 12)
      self.assertEqual(dates[1], datetime.date(2010, 2, 28))
    def test_nonexisting_skip(self):
      gen = self.__nonexistingDays(dateutils.NonExistingDaysHandling.SKIP);
      months = list(date.month for date in gen)
      self.assertEquals(months, [1,3,5,7,8,10,12])
    def test_nonexisting_raise(self):
      self.assertRaises(ValueError, lambda: \
        list(self.__nonexistingDays(dateutils.NonExistingDaysHandling.RAISE)))

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
        nonexistingDaysHandling=dateutils.NonExistingDaysHandling.SKIP)
      dates = list(itertools.islice(cond.scan(self.startDate), 2))
      self.assertEqual(dates, [
        datetime.date(2012, 2, 29),
        datetime.date(2016, 2, 29),
      ])
    def test_nonexisting_start_weekday(self):
      cond = SimpleDateCondition(None, 2, 29, weekdays=[6],
        nonexistingDaysHandling=dateutils.NonExistingDaysHandling.SKIP)
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
      dates = list(SimpleDateCondition(2010, 9, 1, weekdays=[0,2,6]).scan(self.startDate))
      self.assertEqual(dates, [datetime.date(2010, 9, 1)])
    def test_fixed_weekdays_failure(self):
      dates = list(SimpleDateCondition(2010, 9, 1, weekdays=[1,3]).scan(self.startDate))
      self.assertEqual(dates, [])


class RepeatDateCondition(DateCondition):
  '''Класс, бесконечно отсчитывающий заданное количество дней (период) от
  начальной даты.  Направление отсчёта совпадает с направлением сканирования
  (то есть шаг положительный при сканировании в направлении будущего и
  отрицательный при сканировании в направлении прошлого).

  Особенно полезен при использовании внутри объекта класса
  L{CombinedDateCondition}.'''

  def __init__(self, period):
    '''Конструктор

    @param period: Ненулевой период.  Если отрицательный, отсчёт дат ведётся от
    стартовой даты в направлении, противоположном направлению сканирования.
    '''
    if period == 0:
      raise ValueError('Period must not be zero')
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
    '''Набор unit-тестов'''

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
  '''Класс-декоратор, применяющий заданное смещение к результатам, которые
  выдаёт нижележащий объект'''

  def __init__(self, cond, shift):
    '''Конструктор

    @param cond: нижележащий объект класса L{DateCondition}
    @param shift: целочисленное число,задающее смещение в днях
    '''
    super(ShiftDateCondition, self).__init__()
    self.cond = cond
    self.timedelta = datetime.timedelta(days=shift)

  def scan(self, startDate):

    if self.timedelta.days > 0:
      stack = []
      gen = self.cond.scanBack(startDate - datetime.timedelta(days=1))
      for date in itertools.takewhile(
          lambda date: date >= startDate,
          (date + self.timedelta for date in gen)):
        stack.append(date)
      while len(stack) > 0:
        yield stack.pop()

    gen = (date + self.timedelta for date in self.cond.scan(startDate))
    if self.timedelta.days < 0:
      gen = itertools.dropwhile(lambda date: date < startDate, gen)
    for date in gen:
      yield date

  def scanBack(self, startDate):

    if self.timedelta.days < 0:
      stack = []
      gen = self.cond.scan(startDate + datetime.timedelta(days=1))
      for date in itertools.takewhile(
          lambda date: date <= startDate,
          (date + self.timedelta for date in gen)):
        stack.append(date)
      while len(stack) > 0:
        yield stack.pop()

    gen = (date + self.timedelta for date in self.cond.scanBack(startDate))
    if self.timedelta.days > 0:
      gen = itertools.dropwhile(lambda date: date > startDate, gen)
    for date in gen:
      yield date


  class Test(unittest.TestCase):
    '''Набор unit-тестов'''

    def setUp(self):
      self.startDate = datetime.date(2010, 3, 31)

    def test_basic(self):
      cond = ShiftDateCondition(SimpleDateCondition(None, None, 13, weekdays=[4]), -4)
      mondaysPrecedingFriday13th = cond.scan(self.startDate)
      self.assertEqual(list(itertools.islice(mondaysPrecedingFriday13th, 2)), [
        datetime.date(2010, 8, 9),
        datetime.date(2011, 5, 9),
      ])

    def test_wrapStartDate(self):
      cond = ShiftDateCondition(SimpleDateCondition(2010, 4, 1), -5)
      self.assertEqual(list(cond.scan(self.startDate)), [])

    def test_wrapStartDate2(self):
      cond = ShiftDateCondition(SimpleDateCondition(2010, None, 20), 40)
      dates = list(itertools.islice(cond.scan(self.startDate), 3))
      self.assertEqual(dates, [
        datetime.date(2010, 4, 1),
        datetime.date(2010, 4, 29),
        datetime.date(2010, 5, 30),
      ])

    def test_wrapStartDate_back(self):
      cond = ShiftDateCondition(SimpleDateCondition(2010, None, 30), 2)
      date = iter(cond.scanBack(self.startDate)).next()
      self.assertEqual(date, datetime.date(2010, 3, 2))

    def test_wrapStartDate_back2(self):
      cond = ShiftDateCondition(SimpleDateCondition(None, None, 1), -40)
      dates = list(itertools.islice(cond.scanBack(self.startDate), 3))
      self.assertEqual(dates, [
        datetime.date(2010, 3, 22),
        datetime.date(2010, 2, 20),
        datetime.date(2010, 1, 20),
      ])


class SatisfyDateCondition(DateCondition):
  '''Класс-декоратор, возвращающий из результатов, которые выдаёт нижележащий
  объект, только даты, удовлетворяющие условию'''

  def __init__(self, cond, satisfy):
    '''Конструктор

    @param cond: Нижележащий объект класса L{DateCondition}.  Если передан
      C{None}, делается полный перебор дат.
    @param satisfy: Функция обратного вызова, которой будут передаваться
      объекты класса C{datetime.date}.  Функция должна возвращать C{True} или
      C{False} в зависимости от того, нужно или нет включать дату в результат.
    '''
    super(SatisfyDateCondition, self).__init__()
    self.cond = cond
    self.satisfy = satisfy

  def scan(self, startDate):
    return self.__scan(startDate)

  def scanBack(self, startDate):
    return self.__scan(startDate, back=True)

  def __scan(self, startDate, back=False):
    '''Общая реализация для методов L{scan} и L{scanBack}

    @param startDate: объект класса C{datetime.date}, задающий начальную дату
      для поиска
    @param back: если C{True}, поиск выполняется в направлении прошлого,
      иначе в направлении будущего
    '''
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
    '''Набор unit-тестов'''

    def setUp(self):
      self.startDate = datetime.date(2010, 7, 16)

    def test_basic(self):
      everyMonday = SimpleDateCondition(2010, None, None, weekdays=[0])
      everySecondMonday = SatisfyDateCondition(everyMonday, self.__Odd())
      gen = iter(everySecondMonday.scan(datetime.date(2010, 1, 1)))
      the2ndMonday = gen.next()
      self.assertEqual(the2ndMonday, datetime.date(2010, 1, 11))
      the20thMonday = itertools.islice(gen, 8, None).next()
      self.assertEqual(the20thMonday, datetime.date(2010, 5, 17))

    def test_none(self):
      everySecondDay = SatisfyDateCondition(None, self.__Odd())
      gen = everySecondDay.scanBack(datetime.date(2009, 12, 31))
      the6thDayBack = itertools.islice(gen, 2, None).next()
      self.assertEqual(the6thDayBack, datetime.date(2009, 12, 26))

    class __Odd(object):
      '''Вспомогательный функтор.  Если порядковый номер вызова нечётный,
      возвращает C{True}, иначе C{False}.  Номера вызовов считаются с единицы,
      то есть при первом вызове будет возвращено C{True}.'''

      def __init__(self):
        object.__init__(self)
        self.switch = 0

      def __call__(self, date):
        self.switch = 1 - self.switch
        return self.switch == 0


class LimitedDateCondition(DateCondition):
  '''Класс-декоратор, вызывающий нижележащий объект ограниченное количество
  раз.  Ограничения задаются в L{конструкторе<LimitedDateCondition.__init__>}.'''

  def __init__(self, cond, from_=None, until=None, maxMatches=None):
    '''Конструктор

    @param cond: нижележащий объект класса C{DateCondition}
    @param from_: если не C{None}, будут опущены даты меньше этой
    @param until: если не C{None}, будут опущены даты после этой
    @param maxMatches: если не C{None}, количество возвращаемых дат будет
      ограничено этим числом
    '''
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
      gen = itertools.takewhile(lambda date: date >= self.from_, gen)
    if self.maxMatches is not None:
      gen = itertools.islice(gen, self.maxMatches)
    return gen


class CombinedDateCondition(DateCondition):
  '''Класс-декторатор, позволяющий скомбинировать два нижележащих объекта:
  второй вызывается каждый раз, когда очередную дату возвращает первый, при
  этом эта дата передаётся второму объекту в качестве стартовой.'''

  def __init__(self, cond, cond2, scanBack=False):
    '''Конструктор

    @param cond: первый объект класса L{DateCondition}
    @param cond2: второй объект класса L{DateCondition}

    @see: L{CombinedDateCondition}
    '''
    super(CombinedDateCondition, self).__init__()
    self.cond = cond
    self.cond2 = cond2

  def scan(self, startDate):
    return self.__scan(startDate, False)

  def scanBack(self, startDate):
    return self.__scan(startDate, True)

  def __scan(self, startDate, back=False):
    if back:
      try:
        # take ONE step back on the first DateCondition
        date = iter(self.__applyCond(startDate, back)).next()
      except StopIteration:
        pass
      else:
        # run the second DateCondition forward and reverse the result
        gen = self.__applyCond2(date)
        gen = itertools.takewhile(lambda date: date <= startDate, gen)
        # use a temporary list for reversion because using built-in
        # reversed() function on a `takewhile` object leads to an error
        dates = list(gen)
        dates.reverse()
        for date2 in dates:
          yield date2
    else:

      dates = iter(self.__applyCond(startDate, back))
      try:
        firstDate = next(dates)
      except StopIteration:
        firstDate = None

      if firstDate is None or firstDate != startDate:
        try:
          lastDate = iter(self.__applyCond(startDate, not back)).next()
        except StopIteration:
          pass
        else:

          # here's what all checks are made for: handle one step back
          gen = self.__applyCond2(lastDate)
          acceptableDate = lambda date, startDate: date >= startDate if not back \
            else lambda date, startDate: date <= startDate
          gen = itertools.dropwhile(lambda date: not acceptableDate(date, startDate), gen)
          if firstDate is not None:
            gen = itertools.takewhile(lambda date: not acceptableDate(date, firstDate), gen)
          for date2 in gen:
            yield date2

      if firstDate is not None:
        for date2 in self.__applyCond2(firstDate):
          yield date2
        for date in dates:
          for date2 in self.__applyCond2(date):
            yield date2

  def __applyCond(self, date, back=False):
    return self.cond.scan(date) if not back \
      else self.cond.scanBack(date)

  def __applyCond2(self, date):
    return self.cond2.scan(date)


  class Test(unittest.TestCase):
    '''Набор unit-тестов'''

    def setUp(self):
      self.startDate = datetime.date(2010, 3, 31)

    def test_combinedRepeat(self):
      dates = CombinedDateCondition(
        SimpleDateCondition(2010, 9, 23),
        RepeatDateCondition(10)).scan(self.startDate)
      self.assertEqual(list(itertools.islice(dates, 3)), [
        datetime.date(2010, 9, 23),
        datetime.date(2010, 10, 3),
        datetime.date(2010, 10, 13),
      ])

    def test_fullBackward(self):
      dates = CombinedDateCondition(
        SimpleDateCondition(2010, 3, 15),
        RepeatDateCondition(3)).scan(datetime.date(2010, 3, 21))
      self.assertEqual(list(itertools.islice(dates, 3)), [
        datetime.date(2010, 3, 21),
        datetime.date(2010, 3, 24),
        datetime.date(2010, 3, 27),
      ])

    def test_partiallyBackward(self):
      dates = CombinedDateCondition(
        SimpleDateCondition(2010, None, 8),
        RepeatDateCondition(8)).scan(datetime.date(2010, 3, 22))
      self.assertEqual(list(itertools.islice(dates, 4)), [
        datetime.date(2010, 3, 24),
        datetime.date(2010, 4, 1),
        datetime.date(2010, 4, 8),
        datetime.date(2010, 4, 16),
      ])


from StringParser import DateConditionParser


if __name__ == '__main__':
  unittest.main()
