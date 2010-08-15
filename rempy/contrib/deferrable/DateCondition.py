import datetime
import itertools
import unittest

from rempy.DateCondition import DateCondition, SimpleDateCondition
from rempy.Runner import RunnerMode


class DeferrableDateCondition(DateCondition):

  def __init__(self, cond, runnerMode, doneDate=None, advanceWarningValue=0):
    if advanceWarningValue < 0:
      raise ValueError('Advance warning value must not be negative')
    super(DeferrableDateCondition, self).__init__()
    self.cond = cond
    self.mode = runnerMode
    self.doneDate = doneDate
    self.adv = advanceWarningValue

  def scan(self, startDate):
    gen = self.cond.scan(startDate)
    if self.doneDate is not None:
      gen = itertools.dropwhile(lambda date: self.doneDate >= date, gen)

    if self.mode == RunnerMode.REMIND:
      # necessarily remind about an undone event (lastUndone)

      try:
        backDate = startDate - datetime.timedelta(days=1)
        lastUndone = self.cond.scanBack(backDate).next()
      except StopIteration:
        lastUndone = None
      if lastUndone is not None \
          and self.doneDate is not None \
          and self.doneDate >= lastUndone:
        lastUndone = None

      try:
        first = gen.next()
      except StopIteration:
        first = None

      if lastUndone is not None and (first is None or \
          first > startDate + datetime.timedelta(self.adv)):
        yield lastUndone
      if first is not None:
        yield first

    for date in gen:
      yield date

  def scanBack(self, startDate):
    raise NotImplementedError()

  def __getattr__(self, name):
    return getattr(self.cond, name)


  class Test(unittest.TestCase):

    def setUp(self):
      self.startDate = datetime.date(2010, 5, 12)
      self.simpleCond = SimpleDateCondition(2010, None, 14)

    def __simpleTest(self, firstReturnedDate, runnerMode=RunnerMode.REMIND, *args, **kwargs):
      cond = DeferrableDateCondition(self.simpleCond, runnerMode, *args, **kwargs)
      date = cond.scan(self.startDate).next()
      self.assertEquals(date, firstReturnedDate)


    def test_undone(self):
      self.__simpleTest(datetime.date(2010, 4, 14))

    def test_done(self):
      self.__simpleTest(datetime.date(2010, 5, 14),
        doneDate=datetime.date(2010, 4, 14))

    def test_doneEarly(self):
      self.__simpleTest(datetime.date(2010, 4, 14),
        doneDate=datetime.date(2010, 4, 12))

    def test_doneLate(self):
      self.__simpleTest(datetime.date(2010, 5, 14),
        doneDate=datetime.date(2010, 4, 16))

    def test_doneInFuture(self):
      self.__simpleTest(datetime.date(2010, 12, 14),
        doneDate=datetime.date(2010, 11, 14))

    def test_advanceWarning(self):
      self.__simpleTest(datetime.date(2010, 5, 14),
        advanceWarningValue=2)

    def test_eventsMode(self):
      self.__simpleTest(datetime.date(2010, 5, 14),
        RunnerMode.EVENTS)
