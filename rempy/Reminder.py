from Action import MessagePrinter
from DateCondition import SatisfyDateCondition
from StringParser import DateConditionParser, ReminderParser
from utils import FormatError


class Reminder(object):

  def condition(self, runnerMode):
    raise NotImplementedError()

  def advanceWarningValue(self):
    raise NotImplementedError()

  def execute(self, date):
    raise NotImplementedError()


class BasicReminder(Reminder):

  def __init__(self, dateCondition, action, advanceWarningValue=0):
    if advanceWarningValue < 0:
      raise ValueError('Advance warning value must not be negative')
    super(BasicReminder, self).__init__()
    self.cond = dateCondition
    self.action = action
    self.adv = advanceWarningValue

  def condition(self, runnerMode):
    return self.cond

  def advanceWarningValue(self):
    return self.adv

  def execute(self, date):
    self.action(date)


class ShortcutReminder(BasicReminder):

  def __init__(self, dateCondition, action, advanceWarningValue=0, satisfy=None):
    if isinstance(dateCondition, basestring):
      dateCondition = DateConditionParser().parse(dateCondition)
    if satisfy is not None:
      dateCondition = SatisfyDateCondition(dateCondition, satisfy)
    if isinstance(action, basestring):
      action = MessagePrinter(action)
    super(ShortcutReminder, self).__init__(dateCondition, action, advanceWarningValue)

  @staticmethod
  def fromString(dateCondition, action=None, advanceWarningValue=None, satisfy=None):
    parser = ReminderParser()
    cond = parser.parse(dateCondition)
    return ShortcutReminder.fromParser(parser, cond, action, advanceWarningValue, satisfy)

  @staticmethod
  def fromParser(parser, dateCondition, action=None, advanceWarningValue=None, satisfy=None):
    action2 = parser.message()
    if action is None and action2 is None:
      raise FormatError('Message/action must be specified')
    if action is not None and action2 is not None:
      raise FormatError('Message/action is already specified in reminder string')
    if action2 is not None:
      action = action2

    adv = advanceWarningValue
    adv2 = parser.advanceWarningValue()
    if adv is not None and adv2 is not None:
      raise FormatError('Advance warning value is already specified in reminder string')
    if adv2 is not None:
      adv = adv2
    elif adv is None:
      adv = 0

    return ShortcutReminder(dateCondition, action, adv, satisfy)


rem = ShortcutReminder.fromString
