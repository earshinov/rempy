# -*- coding: utf-8 -*-

'''Содержит класс L{DeferrableReminder}'''

from rempy.Reminder import Reminder, ShortcutReminder
from rempy.StringParser import ReminderParser

from DateCondition import DeferrableDateCondition
from StringParser import DeferrableParser


class DeferrableReminder(Reminder):
  '''Класс-декоратор, отслеживающий дату последнего выполнения события,
  связанного с напоминалкой.  Более подробное описание поведения см. в
  документации L{DeferrableDateCondition<DateCondition.DeferrableDateCondition>}.

  @see: L{DeferrableDateCondition<DateCondition.DeferrableDateCondition>}
  '''

  def __init__(self, reminder, doneDate):
    '''Конструктор

    @param reminder: оборачиваемый объект класса L{Reminder<rempy.Reminder.Reminder>}
    @param doneDate: объект класса C{datetime.date}, задающий дату последнего выполнения, или C{None}
    '''
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
    '''Альтернативный метод конструирования объекта класса L{DeferrableReminder}.
    Позволяет задать всё одной строкой.  Формат строки описан в документации
    парсера L{DeferrableParser<StringParser.DeferrableParser>}.

    @param dateCondition: строка для разбора
    @param doneDate: Если не C{None} и в строке C{dateCondition} не задана дата
      последнего выполнения, в качестве такой даты будет использовано значение
      этого параметра.  Параметр должен быть объектом класса C{datetime.date}.

    @param chainReminderFactory: Фабрика для создания оборачиваемого объекта,
      которой будут переданы

        - объект класса L{StringParser<rempy.StringParser.StringParser>}
        - объект класса L{DateCondition<rempy.DateCondition.DateCondition>}
        - дополнительные параметры C{args} и C{kwargs}

      Фактически, в качестве этого параметра можно использовать метод
      C{fromString} из класса, объект которого хочется обернуть.

    @param chainParserFactory: Фабрика для создания парсера, который можно
      передать в C{chainReminderFactory}

    @param args: дополнительные параметры, которые будут переданы в C{chainReminderFactory}
    @param kwargs: дополнительные параметры, которые будут переданы в C{chainReminderFactory}
    @returns: объект класса L{DeferrableReminder}

    @see: L{DeferrableParser<StringParser.DeferrableParser>}
    '''
    parser = DeferrableParser(chainFactory=chainParserFactory)
    cond = parser.parse(dateCondition)
    return DeferrableReminder.fromParser(parser, cond, doneDate,
      chainReminderFactory, *args, **kwargs)

  @staticmethod
  def fromParser(parser, dateCondition, doneDate=None,
      chainReminderFactory=ShortcutReminder.fromParser, *args, **kwargs):
    '''Вспомогательный метод для конструирования объекта класса
    L{DeferrableReminder}.  Слабо полезен конечному пользователю, но может
    быть необходим для реализации сторонних классов напоминалок.

    @param parser: объект класса L{ReminderParser<rempy.StringParser.StringParser>}
    @param dateCondition: объект класса L{DateCondition<rempy.DateCondition.DateCondition>}
    @param doneDate: см. документацию L{fromString}
    @param chainReminderFactory: см. документацию L{fromString}
    @param args: см. документацию L{fromString}
    @param kwargs: см. документацию L{fromString}

    @returns: объект класса L{DeferrableReminder}
    '''
    done = parser.doneDate()
    done2 = doneDate
    if done is not None and done2 is not None:
      raise FormatError('Done date is already specified in reminder string')
    if done is None:
      done = done2

    chainReminder = chainReminderFactory(parser, dateCondition, *args, **kwargs)
    return DeferrableReminder(chainReminder, done)


deferrable = DeferrableReminder.fromString
'''Короткое имя для вызова L{DeferrableReminder.fromString}'''
