'''Содержит иерархию классов L{StringParser}.  Полезен разработчикам классов
напоминалок, в том числе разработчикам расширений.  Конечным пользователям
должен быть необходим редко.

При запуске из командной строки запускает присутствующие в модуле unit-тесты.'''

import copy
import datetime
import unittest

from .utils import FormatError
from .utils.functional import find_not_if
from .utils import dates as dateutils
from .utils import strings


def parseDate(token):
  '''Вспомогательная функция для разбора даты в формате ISO.

  @param token: строка даты в формате ISO
  @returns: объект класса C{datetime.date}
  @raise L{FormatError<utils.FormatError>}: строка имеет неправильный формат
  '''
  try:
    return dateutils.parseIsoDate(token.string())
  except ValueError as e:
    raise FormatError('at "%s": Can\'t parse date: %s' % (token, e.message))


class DateNamedOptionParser:
  '''Класс для разбора длинной опции, в которой лежит один токен,
  содержащий дату в формате ISO

  Использование:

    - добавить в список L{namedOptionHandlers<ChainData.namedOptionHandlers>}
      объекта класса L{ChainData}
    - выполнить разбор строки
    - вызвать метод L{value} для получения считанного значения
  '''

  def __init__(self):
    super(DateNamedOptionParser, self).__init__()
    self.val = None

  def __call__(self, token, tokens):
    if self.val is not None:
      raise FormatError('at "%s": "%s" already specified' % (token, self.name))
    self.val = parseDate(token)
    try:
      token = next(tokens)
    except StopIteration:
      token = None
      pass
    return token

  def value(self):
    '''Получить считанное значение

    @returns: считанное значение как объект класса C{datetime.date} или
      C{None}, если парсер не вызывался (опция отсутствовала во входной строке)
    '''
    return self.val


class ChainData:
  '''Вспомогательный класс для хранения параметров, которые могут передаваться в
  объект класса L{DateConditionParser} и использоваться там для расширения
  набора конструкций, поддерживаемых парсером

  @ivar optionHandlers: Обработчики коротких опций.  Каждый элемент списка
    должен представлять из себя кортеж из двух элементов.  Первый элемент
    кортежа должен быть строкой, задающей начало конструкции.  Второй элемент
    кортежа должен быть функцией, принимающей единственным параметром токен.

  @ivar namedOptionHandlers: Словарь обработчиков длинных опций.  Ключом
    должна быть строка названия опции; значением — функция-обработчик.
    Функция должна принимать два параметра:

      - токен, следующий за токеном, содержащим название опции,
        или C{None}, если токены закончились;
      - Iterator по токенам, установленный на следующий токен.

    Функция должна возвращать токен, следующий за последним обработанным.
    Если токены кончаются, должен быть возвращён C{None}.  Iterable,
    переданный через параметры, должен быть установлен на следующий токен.

  @ivar unparsedRemainderHandler: Если не C{None}, обработчик, который вызывается
    в случае, если в исходной строке остались неразобранные токены.  Функция
    должна принимать параметры:

      - сконструированный к этому моменту объект класса
        L{DateCondition<DateCondition.DateCondition>};
      - первый неразобранный токен;
      - Iterable по токенам, установленный на следующий токен;
      - неразобранная часть строки.

    Функция должна возвращать объект класса
    L{DateCondition<DateCondition.DateCondition>}.

    Пример обработчика: L{DateNamedOptionParser}.

  @see: L{DateConditionParser}
  '''

  def __init__(self, optionHandlers=[], namedOptionHandlers={}, unparsedRemainderHandler=None):
    '''Конструктор.  Выполняет defensive copying переданных коллекций.

    @param optionHandlers: значение для записи в атрибут
      L{optionHandlers<ChainData.optionHandlers>}
    @param namedOptionHandlers: значение для записи в атрибут
      L{namedOptionHandlers<ChainData.namedOptionHandlers>}
    @param unparsedRemainderHandler: значение для записи в атрибут
      L{unparsedRemainderHandler<ChainData.unparsedRemainderHandler>}
    @see: L{DateConditionParser}
    '''
    object.__init__(self)
    self.optionHandlers = copy.copy(optionHandlers)
    self.namedOptionHandlers = copy.copy(namedOptionHandlers)
    self.unparsedRemainderHandler = unparsedRemainderHandler

  def __copy__(self):
    return ChainData(self.optionHandlers, self.namedOptionHandlers,
      self.unparsedRemainderHandler)


class StringParser:
  '''Базовый класс для классов, выполняющий разбор строки
  с описанием напоминалки'''

  def parse(self, string):
    '''Выполнить разбор строки

    @param string: строка для разбора
    @returns: объект класса L{DateCondition<DateCondition.DateCondition>}
    @raise L{FormatError<utils.FormatError>}: строка имеет неправильный формат
    '''
    pass


class DateConditionParser(StringParser):
  '''Класс, выполняющий разбор строки с описанием условия на дату

  Формат строки::

    [REM] <DateSpec> <ShortOpts> <LongOpts>
    <DateSpec> :: { <ISO Date> | [ <Weekday> ... ] [ <Year> ] [ <Month> ] [ <Day> ] }
    <ShortOpts> :: { { [ {-|--}<Delta> ] | [ *<Repeat> ] } ... }
    <LongOpts> :: { { [ {FROM|SCANFROM} <ISO Date> ] | [ UNTIL <ISO Date> ] } ... }

  Weekday: название дня недели, полное (Wednesday) или краткое (Wed)
  Year: полный номер года
  Month: номер месяца (1-12)
  Day: номер дня (1-31)

  Delta: смещение назад на заданное количество дней, может быть только положительным
  Repeat: повтор с интервалом, равным заданному количеству дней

  Ключевые слова не чувствительны к регистру

  Отличия от Remind:

    - Дни недели указываются в начале строки и не могут перемешиваться с
      годом, месяцем и днём
    - Так как не поддерживаются инструкции OMIT, инструкции -<Delta> и --<Delta>
      абсолютно эквивалентны
    - Можно использовать <Repeat> и в случае, когда дата не фиксирована (то есть
      отсутствует хотя бы один из параметров <Year>, <Month>, <Date>), хотя
      в этом мало смысла
    - инструкции FROM и SCANFROM эквивалентны

  В остальном обработка выражения производится согласно поведению Remind.
  '''

  def __init__(self, chainData=None):
    '''Конструктор

    @param chainData: объект класса L{ChainData}
    '''
    super(DateConditionParser, self).__init__()
    self.chainData = copy.copy(chainData) if chainData is not None else ChainData()

  def parse(self, string):
    '''Выполнить разбор строки

    @param string: строка для разбора
    @returns: объект класса L{DateCondition<DateCondition.DateCondition>}
    @raise L{FormatError}: строка имеет неправильный формат
    '''
    tokens = (token.lower() for token in strings.splitWithPositions(string))

    try:
      token = next(tokens)
      if token == 'rem':
        token = next(tokens)
    except StopIteration:
      return SimpleDateCondition()

    token, cond = self._parseDateSpec(token, tokens)
    if token is None:
      return cond

    deltaParser = self._DeltaParser()
    repeatParser = self._RepeatParser()
    optionHandlers = self.chainData.optionHandlers
    optionHandlers += [
      ('-', deltaParser),
      ('*', repeatParser),
    ]
    token = self._parseOptions(token, tokens, optionHandlers)
    cond = deltaParser.apply(cond)
    cond = repeatParser.apply(cond)
    if token is None:
      return cond

    fromParser = DateNamedOptionParser()
    untilParser = DateNamedOptionParser()
    namedOptionHandlers = self.chainData.namedOptionHandlers
    namedOptionHandlers.update({
      'from': fromParser,
      'startfrom': fromParser,
      'until': untilParser,
    })
    token = self._parseNamedOptions(token, tokens, namedOptionHandlers)

    if fromParser.value() is not None or untilParser.value() is not None:
      cond = LimitedDateCondition(cond,
        from_=fromParser.value(), until=untilParser.value())
    if token is None:
      return cond

    if self.chainData.unparsedRemainderHandler is None:
      raise FormatError('Unparsed remainder starting with "%s"' % token)
    else:
      return self.chainData.unparsedRemainderHandler(cond, token, tokens, string)


  class _SimpleDate:
    '''Класс, который умеет конструировать объект класса
    L{DateCondition<DateCondition.DateCondition>} по значением года, месяца,
    дня и списку дней недели.  Установка этих параметров осуществляется
    записью в атрибуты.

    @ivar weekdays: список дней недели (0 - понеделиник, 6 - воскресенье) или C{None} (умолчание)
    @ivar year: полный номер года или C{None} (умолчание)
    @ivar month: номер месяца (1-12) или C{None} (умолчание)
    @ivar day: номер дня (1-31) или C{None} (умолчание)
    '''

    def __init__(self):
      '''Конструктор, заполняющий все атрибуты значениями по умолчанию'''
      object.__init__(self)
      self.weekdays = None
      self.day = None
      self.month = None
      self.year = None

    def createCondition(self):
      '''Создать исходя из значений атрибутов объект класса
      L{DateCondition<DateCondition.DateCondition>}'''
      if self.day is not None and self.weekdays is not None:
        # handle this case like remind
        return CombinedDateCondition(
          SimpleDateCondition(self.year, self.month, self.day),
          LimitedDateCondition(maxMatches=1, \
            cond=SimpleDateCondition(weekdays=self.weekdays)))
      else:
        return SimpleDateCondition(self.year, self.month, self.day, self.weekdays)

  def _parseDateSpec(self, token, tokens):
    ret = self._SimpleDate()
    token, ret.weekdays = self._parseWeekdays(token, tokens)
    if token is not None:
      token, ret.year, ret.month, ret.day = self._parseDate(token, tokens)
    return (token, ret.createCondition())

  def _parseWeekdays(self, token, tokens):
    weekday_names = (
      ('mon', 'monday'),
      ('tue', 'tuesday'),
      ('wed', 'wednesday'),
      ('thu', 'thursday'),
      ('fri', 'friday'),
      ('sat', 'saturday'),
      ('sun', 'sunday'),
    )

    weekdays_set = set()
    def handle_weekday(token):
      token = str(token)
      for weekday, names in enumerate(weekday_names):
        if token in names:
          weekdays_set.add(weekday)
          return True
      return False

    token = find_not_if(itertools.chain((token,), tokens), handle_weekday)
    return (token, list(weekdays_set) if len(weekdays_set) > 0 else None)

  def _parseDate(self, token, tokens):
    months = (
      ('jan', 'january'),
      ('feb', 'february'),
      ('mar', 'march'),
      ('apr', 'april'),
      ('may'),
      ('jun', 'june'),
      ('jul', 'july'),
      ('aug', 'august'),
      ('sep', 'september'),
      ('oct', 'october'),
      ('nov', 'november'),
      ('dec', 'december')
    )

    year = month = day = None
    try:
      while True:
        if token[0].isdigit():
          try:
            i = int(token.string())
          except ValueError:
            d = parseDate(token)
            year, month, day = d.year, d.month, d.day
          else:
            if i < 1000:
              if day is not None:
                raise FormatError('at "%s": Day already specified' % token)
              day = i
            else:
              if year is not None:
                raise FormatError('at "%s": Year already specified' % token)
              year = i
        elif token[0].isalpha():
          found_mon = None
          for mon, names in enumerate(months):
            if token.string() in names:
              found_mon = mon
          if found_mon is None:
            break
          if month is not None:
            raise FormatError('at "%s": Month already specified' % token)
          month = found_mon + 1
        else:
          break
        token = next(tokens)
    except StopIteration:
      token = None
      pass
    return (token, year, month, day)


  def _parseOptions(self, token, tokens, handlers):
    '''Разобрать короткие опции'''
    try:
      while True:
        handler = None
        for substr, h in handlers:
          if token.startswith(substr):
            handler = h
            break
        if handler is None:
          break
        handler(token)
        token = next(tokens)
    except StopIteration:
      token = None
      pass
    return token

  class _DeltaParser:
    '''Парсер короткой опции <Delta>

    Использование:

      - добавить в список L{optionHandlers<ChainData.optionHandlers>}
        объекта класса L{ChainData}
      - выполнить разбор строки
      - вызвать метод L{apply} для применения параметра <Delta> к объекту
        класса L{DateCondition<DateCondition.DateCondition>}
    '''

    def __init__(self):
      object.__init__(self)
      self.delta = 0

    def __call__(self, token):
      error = False
      try:
        start = 2 if token[1] == '-' else 1
        delta = int(token[start:].string())
        if delta < 0:
          raise ValueError()
      except IndexError:
        error = True
      except ValueError:
        error = True
      if error:
        raise FormatError('at "%s": Can\'t parse delta' % token)
      else:
        self.delta = delta

    def apply(self, cond):
      '''Применить параметр <Delta> к объекту класса
      L{DateCondition<DateCondition.DateCondition>}

      @param cond: объект класса L{DateCondition<DateCondition.DateCondition>}
      @returns: новый объект класса L{DateCondition<DateCondition.DateCondition>}
        или C{cond}, если парсер не вызывался (в строке не был указан параметр <Delta>).
      '''
      return cond if self.delta == 0 else \
        ShiftDateCondition(cond, -self.delta)

  class _RepeatParser:
    '''Парсер короткой опции <Repeat>

    Использование:

      - добавить в список L{optionHandlers<ChainData.optionHandlers>}
        объекта класса L{ChainData}
      - выполнить разбор строки
      - вызвать метод L{apply} для применения параметра <Repeat> к объекту
        класса L{DateCondition<DateCondition.DateCondition>}
    '''

    def __init__(self):
      object.__init__(self)
      self.repeat = None

    def __call__(self, token):
      error = False
      try:
        repeat = int(token[1:].string())
        if repeat <= 0:
          raise ValueError()
      except ValueError:
        raise FormatError('at "%s": Can\'t parse repeat' % token)
      else:
        self.repeat = repeat

    def apply(self, cond):
      '''Применить параметр <Repeat> к объекту класса
      L{DateCondition<DateCondition.DateCondition>}

      @param cond: объект класса L{DateCondition<DateCondition.DateCondition>}
      @returns: новый объект класса L{DateCondition<DateCondition.DateCondition>}
        или C{cond}, если парсер не вызывался (в строке не был указан параметр <Repeat>).
      '''
      return cond if self.repeat is None else \
        CombinedDateCondition(cond, RepeatDateCondition(self.repeat))


  def _parseNamedOptions(self, token, tokens, handlers):
    '''Разобрать длинные опции'''
    while True:
      handler = handlers.get(token)
      if handler is None:
        break
      try:
        token = next(tokens)
      except StopIteration:
        raise FormatError('Unexpected end')
      token = handler(token, tokens)
      if token is None:
        break
    return token


  class Test(unittest.TestCase):
    '''Набор unit-тестов'''

    def setUp(self):
      self.parser = DateConditionParser()
      self.startDate = datetime.date(2010, 1, 1)

    def test_shortDateFormat(self):
      gen = self.parser.parse('REM 2010-06-12').scan(datetime.date(2010, 6, 12))
      self.assertEqual(list(gen), [datetime.date(2010, 6, 12)])

    def test_fromUntil(self):
      s = 'Mon Wed Jan FROM 2010-01-12 UNTIL 2011-01-10'
      gen = self.parser.parse(s).scan(self.startDate)
      self.assertEqual(list(gen), [
        datetime.date(2010, 1, 13),
        datetime.date(2010, 1, 18),
        datetime.date(2010, 1, 20),
        datetime.date(2010, 1, 25),
        datetime.date(2010, 1, 27),
        datetime.date(2011, 1,  3),
        datetime.date(2011, 1,  5),
        datetime.date(2011, 1, 10),
      ])

    def test_shiftRepeat(self):
      s = 'June 12 2010 --12 *5'
      gen = self.parser.parse(s).scan(self.startDate)
      self.assertEqual(list(itertools.islice(gen, 3)), [
        datetime.date(2010, 5, 31),
        datetime.date(2010, 6, 5),
        datetime.date(2010, 6, 10),
      ])

    def test_weekdaysWithDay1(self):
      s = 'Wed 1'
      firstWedEveryMonth = self.parser.parse(s).scan(self.startDate)
      self.assertEqual(list(itertools.islice(firstWedEveryMonth, 4)), [
        datetime.date(2010, 1, 6),
        datetime.date(2010, 2, 3),
        datetime.date(2010, 3, 3),
        datetime.date(2010, 4, 7),
      ])
    def test_weekdaysWithDay2(self):
      s = 'Wed Fri 2010-06-12'
      dates = list(self.parser.parse(s).scan(self.startDate))
      self.assertEqual(dates, [datetime.date(2010, 6, 16)])

    def test_formatError(self):
      s = '2010-01-12 **5'
      self.assertRaises(FormatError, lambda: self.parser.parse(s))

    def test_unparsedRemainder(self):
      s = 'REM 2010-01-12 MSG Unparsed remainder'
      self.assertRaises(FormatError, lambda: self.parser.parse(s))


class ReminderParser(StringParser):
  '''Класс-декоратор для разбора строки напоминалки с базовыми параметрами

  К опциям, которые поддерживает обёрнутый класс, добавляется короткая
  опция C{{+|++}<AdvanceWarning>}.  В отличие от Remind, мы не поддерживаем
  инструкции типа OMIT, поэтому C{+} и C{++} равнозначны.

  Конечная часть строки, не разобранная в обёрнутом классе, считается сообщением
  для вывода.  Опционально в начале сообщения можно использовать ключевое слово MSG.

  Использование:
    - сконструировать объект
    - вызвать L{parse}
    - использовать возвращённое значение и значения, которые возвращают
      методы L{advanceWarningValue} и L{message}
  '''

  class _AdvanceWarningParser:
    '''Парсер для короткой опции <AdvanceWarningValue>

    Использование:
      - добавить в список L{optionHandlers<ChainData.optionHandlers>}
        объекта класса L{ChainData}
      - выполнить разбор строки
      - вызвать метод L{advanceWarningValue} для получения считанного значения
    '''

    def __init__(self):
      object.__init__(self)
      self.adv = 0

    def __call__(self, token):
      error = False
      try:
        start = 2 if token[1] == '+' else 1
        adv = int(token[start:].string())
        if adv < 0:
          raise ValueError()
      except IndexError:
        error = True
      except ValueError:
        error = True
      if error:
        raise FormatError('at "%s": Can\'t parse advance warning value' % token)
      else:
        self.adv = adv

    def advanceWarningValue(self):
      '''Получить считанное значение

      @returns: считанное целочисленное значение или C{None}, если парсер
        не вызывался (в строке отсутствовала опция <AdvanceWarning)
      '''
      return self.adv

  def __init__(self, chainFactory=DateConditionParser, chainData=None):
    '''Конструктор

    @param chainFactory: callable, при вызове c параметром C{chainData}
      возвращающий объект класса L{StringParser}, который будет обёрнут
    @param chainData: объект класса L{ChainData}
    '''
    super(ReminderParser, self).__init__()

    chainData = copy.copy(chainData) if chainData is not None else ChainData()
    self.advParser = self._AdvanceWarningParser()
    chainData.optionHandlers.append(('+', self.advParser))
    if chainData.unparsedRemainderHandler is not None:
      raise ValueError('There is already unparsed remainder handler in chainData')
    chainData.unparsedRemainderHandler = self._handleUnparsedRemainder
    self.chain = chainFactory(chainData=chainData)
    self.msg = None

  def _handleUnparsedRemainder(self, cond, token, tokens, string):
    '''Обработчик, который записывается в атрибут
    L{unparsedRemainderHandler<ChainData.unparsedRemainderHandler>} объекта
    C{chainData}, переданного в конструктор.  Сохраняет сообщение для вывода.
    '''
    try:
      if token == 'msg':
        token = next(tokens)
    except StopIteration:
      pass
    else:
      self.msg = string[token.position():]
    return cond

  def parse(self, string):
    return self.chain.parse(string)

  def advanceWarningValue(self):
    '''Получить считанное значение опции <AdvanceWarning> или C{None}, если
    эта опция отсутствовала в исходной строке'''
    return self.advParser.advanceWarningValue()

  def message(self):
    '''Получить считанное сообщение для вывода или C{None}, если оно
    отсутствовало в исходной строке'''
    return self.msg


  class Test(unittest.TestCase):
    '''Набор unit-тестов'''

    def setUp(self):
      self.parser = ReminderParser()

    def test_advanceWarning(self):
      self.parser.parse('June 12 +5')
      self.assertEqual(self.parser.advanceWarningValue(), 5)
      self.assertEqual(self.parser.message(), None)

    def test_message(self):
      self.parser.parse('REM Jan 1 MSG New Year')
      self.assertEqual(self.parser.advanceWarningValue(), 0)
      self.assertEqual(self.parser.message(), 'New Year')


from .DateCondition import *


if __name__ == '__main__':
  unittest.main()
