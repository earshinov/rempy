import copy
import datetime
import unittest

from utils import FormatError
import utils.dates as dateutils
import utils.strings as strings


class ChainData(object):

  def __init__(self, optionHandlers=[], namedOptionHandlers={}, unparsedRemainderHandlers=[]):
    object.__init__(self)
    self.optionHandlers = copy.copy(optionHandlers)
    self.namedOptionHandlers = copy.copy(namedOptionHandlers)
    self.unparsedRemainderHandlers = copy.copy(unparsedRemainderHandlers)

  def __copy__(self):
    return ChainData(self.optionHandlers, self.namedOptionHandlers,
      self.unparsedRemainderHandlers)


class StringParser(object):

  def parse(self, string):
    pass


class DateConditionParser(StringParser):

  def __init__(self, chainData=None):
    super(DateConditionParser, self).__init__()
    self.chainData = copy.copy(chainData) if chainData is not None else ChainData()

  # Differences from remind:
  # - week days are specified at the beginning (they can't be mixed with year, month and day);
  # - two-digit years are not supported;
  # - "--" and "-" delta specifications mean the same as "omits" are not supported;
  # - repeat option can be used for non-fixed dates, in this case it will "repeat"
  #   the first match date;
  # - FROM and STARTFROM clauses mean the same.
  def parse(self, string):
    tokens = (token.lower() for token in strings.splitWithPositions(string))

    try:
      token = tokens.next()
      if token == 'rem':
        token = tokens.next()
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

    fromParser = self._DateNamedOptionParser('From')
    untilParser = self._DateNamedOptionParser('Until')
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

    self.chainData.unparsedRemainderHandlers.append(self._handleUnparsedRemainder)
    for h in self.chainData.unparsedRemainderHandlers:
      token, cond = h(cond, token, tokens, string)
      if token is None:
        break
    return cond

  def _handleUnparsedRemainder(self, cond, token, tokens, string):
    raise FormatError('Unparsed remainder starting with "%s"' % token)


  class _SimpleDate(object):

    def __init__(self):
      object.__init__(self)
      self.weekdays = None
      self.day = None
      self.month = None
      self.year = None

    def createCondition(self):
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
    try:
      found = True
      while found:
        found = False
        for weekday, names in enumerate(weekday_names):
          if token in names:
            weekdays_set.add(weekday)
            found = True; token = tokens.next()
    except StopIteration:
      token = None
      pass
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
            d = dateutils.parseIsoDate(token.string())
            if d is None:
              raise FormatError('at "%s": Can\'t parse' % token)
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
        token = tokens.next()
    except StopIteration:
      token = None
      pass
    return (token, year, month, day)


  def _parseOptions(self, token, tokens, handlers):
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
        token = tokens.next()
    except StopIteration:
      token = None
      pass
    return token

  class _DeltaParser(object):

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
      return cond if self.delta == 0 else \
        CombinedDateCondition(cond, ShiftDateCondition(-self.delta))

  class _RepeatParser(object):

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
      return cond if self.repeat is None else \
        CombinedDateCondition(cond, RepeatDateCondition(self.repeat))


  def _parseNamedOptions(self, token, tokens, handlers):
    while True:
      handler = handlers.get(token)
      if handler is None:
        break
      try:
        token = tokens.next()
      except StopIteration:
        raise FormatError('Unexpected end')
      token = handler(token, tokens)
      if token is None:
        break
    return token

  class _DateNamedOptionParser(object):

    def __init__(self, name):
      object.__init__(self)
      self.name = name
      self.val = None

    def __call__(self, token, tokens):
      if self.val is not None:
        raise FormatError('at "%s": "%s" already specified' % (token, self.name))
      self.val = dateutils.parseIsoDate(token.string())
      if self.val is None:
        raise FormatError('at "%s": Can\'t parse date' % token)
      try:
        token = tokens.next()
      except StopIteration:
        token = None
        pass
      return token

    def value(self):
      return self.val


  class Test(unittest.TestCase):

    def setUp(self):
      self.parser = DateConditionParser()
      self.startDate = datetime.date(2010, 1, 1)

    def test_shortDateFormat(self):
      gen = self.parser.parse('REM 2010-06-12').scan(datetime.date(2010, 06, 12))
      self.assertEqual(list(gen), [datetime.date(2010, 06, 12)])

    def test_fromUntil(self):
      str = 'Mon Wed Jan FROM 2010-01-12 UNTIL 2011-01-10'
      gen = self.parser.parse(str).scan(self.startDate)
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
      str = 'June 12 2010 --12 *5'
      gen = self.parser.parse(str).scan(self.startDate)
      self.assertEqual(list(itertools.islice(gen, 3)), [
        datetime.date(2010, 5, 31),
        datetime.date(2010, 6, 5),
        datetime.date(2010, 6, 10),
      ])

    def test_weekdaysWithDay1(self):
      str = 'Wed 1'
      firstWedEveryMonth = self.parser.parse(str).scan(self.startDate)
      self.assertEqual(list(itertools.islice(firstWedEveryMonth, 4)), [
        datetime.date(2010, 1, 6),
        datetime.date(2010, 2, 3),
        datetime.date(2010, 3, 3),
        datetime.date(2010, 4, 7),
      ])
    def test_weekdaysWithDay2(self):
      str = 'Wed Fri 2010-06-12'
      dates = list(self.parser.parse(str).scan(self.startDate))
      self.assertEqual(dates, [datetime.date(2010, 6, 16)])

    def test_formatError(self):
      str = '2010-01-12 **5'
      self.assertRaises(FormatError, lambda: self.parser.parse(str))

    def test_unparsedRemainder(self):
      str = 'REM 2010-01-12 MSG Unparsed remainder'
      self.assertRaises(FormatError, lambda: self.parser.parse(str))


from DateCondition import *


if __name__ == '__main__':
  unittest.main()
