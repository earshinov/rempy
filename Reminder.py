from Action import MessagePrinter
from StringParser import DateConditionParser, ReminderParser
from utils import FormatError


class Reminder(object):

  def condition(self):
    raise NotImplementedError()

  def advanceWarningValue(self):
    raise NotImplementedError()

  def advanceWarningValue(self):
    raise NotImplementedError()


class BasicReminder(Reminder):

  def __init__(self, dateCondition, action, advanceWarningValue=0):
    super(BasicReminder, self).__init__()
    self.cond = dateCondition
    self.action = action
    self.adv = advanceWarningValue

  def condition(self):
    return self.cond

  def advanceWarningValue(self):
    return self.adv

  def execute(self, date):
    self.action(date)


class ShortcutReminder(BasicReminder):

  def __init__(self, dateCondition, action, advanceWarningValue=0):
    if isinstance(dateCondition, basestring):
      dateCondition = DateConditionParser().parse(dateCondition)
    if isinstance(action, basestring):
      action = MessagePrinter(action)
    super(ShortcutReminder, self).__init__(dateCondition, action, advanceWarningValue)

  @staticmethod
  def fromString(dateCondition, action=None, advanceWarningValue=None):
    parser = ReminderParser()
    cond = parser.parse(dateCondition)

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

    return ShortcutReminder(cond, action, adv)


rem = ShortcutReminder.fromString
