# -*- coding: utf-8 -*-

'''Содержит иерархию классов L{Reminder}'''

from Action import MessagePrinter
from DateCondition import SatisfyDateCondition
from StringParser import DateConditionParser, ReminderParser
from utils import FormatError


class Reminder(object):
  '''Базовый класс напоминалки.  Напоминалка объединяет условие, согласно
  которому выбираются даты; действие, которое надо выполнить для каждой даты
  (обычно печать сообщения); количество дней для заблаговременного
  предупреждения о событии.

  Замечания о терминологии:

    - дата называется подпадающей под напоминалку, если она удовлетворяет
      условию, заданному в этой напоминалке;
    - событием называется ситуация, когда заданная дата подпадает под
      определённую напоминалку::

      event = (date, reminder) | date `matches` reminder
  '''

  def condition(self, runnerMode):
    '''Получить условие, согласно которому выбираются даты

    @param runnerMode: константа из «перечисления» L{RunnerMode<Runner.RunnerMode>}
    @returns: объект класса L{DateCondition<DateCondition.DateCondition>}
    '''
    raise NotImplementedError()

  def advanceWarningValue(self):
    '''Очередной getter.

    @returns: целочисленное количество дней для заблаговременного
      предупреждения о событии
    '''
    raise NotImplementedError()

  def execute(self, date):
    '''Вызвать связанное с напоминалкой действие для данной даты

    @param date: объект класса C{datetime.date}
    '''
    raise NotImplementedError()


class BasicReminder(Reminder):
  '''Простейшая реализация класса L{Reminder}'''

  def __init__(self, dateCondition, action, advanceWarningValue=0):
    '''Конструктор

    @param dateCondition: объект класса L{DateCondition<DateCondition.DateCondition>}
    @param action: объект класса L{Action<Action.Action>}
    @param advanceWarningValue: неотрицательное целочисленное значение,
      задающее количество дней для предварительного предупреждения о событии
    '''
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
  '''Простая реализация класса L{Reminder}, которая допускает передачу в
  конструктор строк и выполняет их разбор с использованием модуля
  L{StringParser}.  В большинстве случаев задавать условия строкой намного
  удобнее, чем вручную конструировать нижележащие классы.
  '''

  def __init__(self, dateCondition, action, advanceWarningValue=0, satisfy=None):
    '''Конструктор

    @param dateCondition: Объект класса L{DateCondition<DateCondition.DateCondition>}
      или строка.  В последнем случае условие конструируется с использованием
      объекта класса L{DateConditionParser<StringParser.DateConditionParser>}.
    @param action: Объект класса L{Action<Action.Action>} или строка.  В
      последнем случае в качестве действия используется объект класса
      L{MessagePrinter<Action.MessagePrinter>}, которому заданная строка
      передаётся в качестве сообщения для вывода.
    @param advanceWarningValue: неотрицательное целочисленное значение,
      задающее количество дней для заблаговременного предупреждения о событии.
    @param satisfy: если не C{None}, задаёт функцию для дополнительного отсева
      дат.  Функция должна принимать объект класса C{datetime.date} и возвращать
      C{True} или C{False} в зависимости от того, нужно ли считать дату
      подпадающей под напоминатель.
    '''
    if isinstance(dateCondition, basestring):
      dateCondition = DateConditionParser().parse(dateCondition)
    if satisfy is not None:
      dateCondition = SatisfyDateCondition(dateCondition, satisfy)
    if isinstance(action, basestring):
      action = MessagePrinter(action)
    super(ShortcutReminder, self).__init__(dateCondition, action, advanceWarningValue)

  @staticmethod
  def fromString(dateCondition, action=None, advanceWarningValue=None, satisfy=None):
    '''Альтернативный метод конструирования объекта класса L{ShortcutReminder}.
    Позволяет задать условие, сообщение для вывода и количество дней для
    заблаговременного предупреждения о событии одной строкой.  Формат строки
    описан в документации парсера L{ReminderParser<StringParser.ReminderParser>}.

    @param dateCondition: строка для разбора с использованием объекта класса
      L{ReminderParser<StringParser.ReminderParser>}
    @param action: Если не C{None} и в строке C{dateCondition} не задано
      сообщение для вывода, в качестве действия будет использоваться это.
      Может представлять собой объект класса L{Action<Action.Action>} или
      строку сообщения.
    @param advanceWarningValue: если не C{None} и в строке C{dateCondition} не
      задано количество дней для заблаговременного предупреждения о событии,
      будет использоваться это.  Параметр должен быть неотрицательным целым
      числом.
    @param satisfy: если не C{None}, задаёт функцию для дополнительного отсева дат.
      См. комментарии к соответствующему параметру
      L{конструктора<ShortcutReminder.__init__>}.
    @returns: объект класса L{ShortcutReminder}

    @see: L{ReminderParser<StringParser.ReminderParser>}
    '''
    parser = ReminderParser()
    cond = parser.parse(dateCondition)
    return ShortcutReminder.fromParser(parser, cond, action, advanceWarningValue, satisfy)

  @staticmethod
  def fromParser(parser, dateCondition, action=None, advanceWarningValue=None, satisfy=None):
    '''Вспомогательный метод для конструирования объекта класса
    L{ShortcutReminder}.  Слабо полезен конечному пользователю, но может быть
    необходим для реализации сторонних классов напоминалок.

    @param parser: объект класса L{ReminderParser<StringParser.StringParser>}
    @param dateCondition: объект класса L{DateCondition<DateCondition.DateCondition>}
    @param action: см. документацию L{fromString}
    @param advanceWarningValue: см. документацию L{fromString}
    @param satisfy: см. документацию L{fromString}
    @returns: объект класса L{ShortcutReminder}
    '''
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
