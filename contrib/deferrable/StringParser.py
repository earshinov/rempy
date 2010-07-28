import datetime
import unittest

from rempy.StringParser import StringParser, ReminderParser, ChainData
from rempy.utils.dates import parseIsoDate


class DeferrableParser(StringParser):

  class _DoneParser(object):

    def __init__(self):
      object.__init__(self)
      self.done = None

    def __call__(self, token, tokens):
      self.done = parseIsoDate(token.string())
      if self.done is None:
        raise FormatError('at "%s": Can\'t parse date' % token)
      try:
        token = tokens.next()
      except StopIteration:
        token = None
      return token

    def doneDate(self):
      return self.done

  def __init__(self, chainFactory=ReminderParser, chainData=None):
    super(DeferrableParser, self).__init__()
    chainData = copy.copy(chainData) if chainData is not None else ChainData()
    self.doneParser = self._DoneParser()
    chainData.namedOptionHandlers.update({'done': self.doneParser})
    self.chain = chainFactory(chainData=chainData)

  def parse(self, string):
    return self.chain.parse(string)

  def doneDate(self):
    return self.doneParser.doneDate()

  def __getattr__(self, name):
    return getattr(self.chain, name)


  class Test(unittest.TestCase):

    def setUp(self):
      self.parser = DeferrableParser()

    def test_undone(self):
      str = 'REM 2010-12-10 -5 +5 *5 FROM 2010-12-01 UNTIL 2010-12-31 MSG Message'
      self.parser.parse(str)
      self.assertEqual(self.parser.doneDate(), None)

    def test_done(self):
      str = 'REM 2010-12-10 -5 +5 *5 DONE 2010-12-20 UNTIL 2010-12-31 MSG Message'
      self.parser.parse(str)
      self.assertEqual(self.parser.doneDate(), datetime.date(2010, 12, 20))
