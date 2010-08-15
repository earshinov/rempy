from rempy.Reminder import Reminder, ShortcutReminder
from rempy.StringParser import ReminderParser

from DateCondition import DeferrableDateCondition
from StringParser import DeferrableParser


class DeferrableReminder(Reminder):

  def __init__(self, reminder, doneDate):
    super(DeferrableReminder, self).__init__()
    self.reminder = reminder
    self.doneDate = doneDate

  def condition(self, runnerMode):
    return DeferrableDateCondition(self.reminder.condition(runnerMode),
      runnerMode, self.doneDate, self.advanceWarningValue())

  def advanceWarningValue(self):
    return self.reminder.advanceWarningValue()

  def execute(self, date):
    return self.reminder.execute(date)


  @staticmethod
  def fromString(dateCondition, doneDate=None,
      chainReminderFactory=ShortcutReminder.fromParser,
      chainParserFactory=ReminderParser,
      *args, **kwargs):
    parser = DeferrableParser(chainFactory=chainParserFactory)
    cond = parser.parse(dateCondition)
    return DeferrableReminder.fromParser(parser, cond, doneDate,
      chainReminderFactory, *args, **kwargs)

  @staticmethod
  def fromParser(parser, dateCondition, doneDate=None,
      chainReminderFactory=ShortcutReminder.fromParser, *args, **kwargs):
    done = parser.doneDate()
    done2 = doneDate
    if done is not None and done2 is not None:
      raise FormatError('Done date is already specified in reminder string')
    if done is None:
      done = done2

    chainReminder = chainReminderFactory(parser, dateCondition, *args, **kwargs)
    return DeferrableReminder(chainReminder, done)


deferrable = DeferrableReminder.fromString
