import datetime
import itertools
import unittest

from rempy.DateCondition import DateCondition, SimpleDateCondition


class DeferrableDateCondition(DateCondition):

  def __init__(self, cond, doneDate=None, advanceWarningValue=0):
    super(DeferrableDateCondition, self).__init__()
    self.cond = cond
    self.doneDate = doneDate
    self.adv = advanceWarningValue

  def scan(self, startDate):
    try:
      backDate = startDate - datetime.timedelta(days=1)
      lastUndone = self.cond.scanBack(backDate).next()
    except StopIteration:
      lastUndone = None
    if lastUndone is not None \
        and self.doneDate is not None \
        and self.doneDate >= lastUndone:
      lastUndone = None

    gen = self.cond.scan(startDate)
    if self.doneDate is not None:
      gen = itertools.dropwhile(lambda date: self.doneDate >= date, gen)

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

    def test_undone(self):
      cond = DeferrableDateCondition(self.simpleCond)
      date = cond.scan(self.startDate).next()
      self.assertEquals(date, datetime.date(2010, 4, 14))

    def test_done(self):
      cond = DeferrableDateCondition(self.simpleCond,
        doneDate=datetime.date(2010, 4, 14))
      date = cond.scan(self.startDate).next()
      self.assertEquals(date, datetime.date(2010, 5, 14))

    def test_doneEarly(self):
      cond = DeferrableDateCondition(self.simpleCond,
        doneDate=datetime.date(2010, 4, 12))
      date = cond.scan(self.startDate).next()
      self.assertEquals(date, datetime.date(2010, 4, 14))

    def test_doneLate(self):
      cond = DeferrableDateCondition(self.simpleCond,
        doneDate=datetime.date(2010, 4, 16))
      date = cond.scan(self.startDate).next()
      self.assertEquals(date, datetime.date(2010, 5, 14))

    def test_doneInFuture(self):
      cond = DeferrableDateCondition(self.simpleCond,
        doneDate=datetime.date(2010, 11, 14))
      date = cond.scan(self.startDate).next()
      self.assertEquals(date, datetime.date(2010, 12, 14))

    def test_advanceWarning(self):
      cond = DeferrableDateCondition(self.simpleCond, advanceWarningValue=2)
      date = cond.scan(self.startDate).next()
      self.assertEquals(date, datetime.date(2010, 5, 14))
