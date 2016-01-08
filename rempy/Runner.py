# -*- coding: utf-8 -*-

'''Содержит иерархию классов L{Runner} и функцию L{main}

При запуске из командной строки запускает функцию L{main}.'''

import datetime
import getopt
from heapq import heappop, heappush
import locale
import sys

try:
  from parsedatetime import parsedatetime
  from parsedatetime import parsedatetime_consts
  localeName = locale.getdefaultlocale()[0] # parsedatetime/PyICU do not understand ""
  pdt = parsedatetime.Calendar(parsedatetime_consts.Constants(localeName))
except ImportError:
  pdt = None

import utils.dates as dateutils


def _parseDate(string):
  if pdt is None:
    return dateutils.parseIsoDate(string)
  else:
    try:
      values, flag = pdt.parse(string)
      if flag != 1:
        raise ValueError('Incorrect date string: %s' + string)
      return datetime.date(*values[:3])
    except ValueError, e:
      try:
        return dateutils.parseIsoDate(string)
      except ValueError:
        raise e


class RunnerMode:
  '''Режим запуска'''

  REMIND = 0
  '''Режим напоминания.  Учитывает значения количества дней для предварительного
  оповещения о событии, указанные в напоминалках'''

  EVENTS = 1
  '''Режим вывода списка событий.  В этом режиме объект класса L{Runner} не
  предупреждает о событиях предварительно'''


class Runner(object):
  '''Класс, собирающий список напоминалок и затем выполняющий связанные с ними
  действия в порядке возрастания дат соответствующих событий.  При этом
  выполнение действий и некоторые другие действия делегируются классу-наследнику.

  Использование:

    - сконструировать
    - добавить напоминалки с использованием метода L{add}
    - вызвать метод L{run}
  '''

  def __init__(self):
    super(Runner, self).__init__()
    self.reminders = []

  def add(self, reminder):
    '''Добавить напоминалку

    @param reminder: объект класса L{Reminder<Reminder.Reminder>}
    '''
    self.reminders.append(reminder)

  def run(self, fromDate, toDate, mode):
    '''Запустить связанные с добавленными напоминалками действия для событий
    в пределах заданного диапазона дат

    @param fromDate: объект класса C{datetime.date}, задающий начальную дату
    @param toDate: объект класса C{datetime.date}, задающий конечную дату (включительно)
    @param mode: константа из «перечисления» L{RunnerMode}, задающая режим запуска
    '''
    heap = []

    def __pushNextEvent(ordinal, reminder, gen):
      to = toDate + datetime.timedelta(days=reminder.advanceWarningValue()) \
        if mode == RunnerMode.REMIND else toDate
      try:
        date = gen.next()
      except StopIteration:
        return
      if date <= to:
        heappush(heap, (date, ordinal, reminder, gen))

    for i, reminder in enumerate(self.reminders):
      gen = iter(reminder.condition(mode).scan(fromDate))
      __pushNextEvent(i, reminder, gen)
    currentDate = None
    while len(heap) > 0:
      date, ordinal, reminder, gen = heappop(heap)
      if date != currentDate:
        currentDate = date
        self._handleNextDate(date)
      self._executeReminder(reminder, date)
      __pushNextEvent(ordinal, reminder, gen)

  def _handleNextDate(self, date):
    '''Метод для определения в наследнике.  Вызывается, когда очередное событие
    попадает на дату, которая превышает дату предыдущего события.  Реализация
    по умолчанию ничего не делает.

    @param date: объект класса C{datetime.date}, дата события
    '''
    pass

  def _executeReminder(self, reminder, date):
    '''Метод для определения в наследнике.  Вызывается, когда требуется выполнить
    действие, связанное с напоминалкой. Реализация по умолчанию ничего не делает.

    @param reminder: объект класса L{Reminder<Reminder.Reminder>}
    @param date: объект класса C{datetime.date}, дата события
    '''
    pass


class PrintRunner(Runner):
  '''Наследник класса L{Runner}, подходящий для обработки текстовых
  напоминателей (таких, что связанные с ними действия выполняют печать
  сообщения в поток вывода).'''

  def _handleNextDate(self, date):
    print 'Reminders for %s' % date.isoformat()

  def _executeReminder(self, reminder, date):
    reminder.execute(date)


def main(args=sys.argv, runnerFactory=PrintRunner):
  '''Функция main()

  При выполнении пользовательского файла в него передаются следующие объекты:

    - C{runner} - Объект класса L{Runner}.

    - C{rem} - Функция, добавляющая в C{runner} объект класса
      L{ShortcutReminder<Reminder.ShortcutReminder>}.  Аргументы функции
      передаются в статический метод
      L{ShortcutReminder.fromString<Reminder.ShortcutReminder.fromString>}.

    - C{deferrable} - Функция, добавляющая в C{runner} объект класса
      L{DeferrableReminder<contrib.deferrable.Reminder.DeferrableReminder>}.
      Аргументы функции передаются в статический метод
      L{DeferrableReminder.fromString<contrib.deferrable.Reminder.DeferrableReminder.fromString>}.

  @param args: Аргументы командной строки
  @param runnerFactory: callable, при вызове без параметров возвращающий объект
    класса L{Runner}, который будет использоваться для запуска напоминалок
  @returns: код возврата: 0 при успешном выполнении, 1 в случае ошибки
  '''
  assert len(args) > 0

  locale.setlocale(locale.LC_ALL, '')

  USAGE = '''Usage: %s COMMAND OPTIONS FILENAMES\n
COMMAND = { remind | events }
OPTIONS = [ --from=DATE ] [ --to=DATE | --future=N_DAYS ]''' % args[0]

  if len(args) < 2:
    print >> sys.stderr, 'A command is required'
    print >> sys.stderr, USAGE
    return 1

  if args[1] == 'remind':
    mode = RunnerMode.REMIND
  elif args[1] == 'events':
    mode = RunnerMode.EVENTS
  else:
    print >> sys.stderr, 'Unknown command: "%s"' % args[1]
    print >> sys.stderr, USAGE
    return 1

  try:
    longopts = ['help', 'usage', 'from=', 'to=', 'future=']
    options, args = getopt.gnu_getopt(args[2:], 'h', longopts)
  except getopt.GetoptError, err:
    print >> sys.stderr, `err`
    print >> sys.stderr, USAGE
    return 1

  if len(args) == 0:
    print >> sys.stderr, 'Filename is required'
    print >> sys.stderr, USAGE
    return 1

  from_ = datetime.date.today()
  to = future = None
  for option, value in options:
    if option in ('-h', '--help', '--usage'):
      print USAGE
      return 0
    elif option == '--from':
      try:
        from_ = _parseDate(value)
      except ValueError:
        print >> sys.stderr, 'Can\'t parse date %s' % value
        return 1
    elif option == '--to':
      future = None
      to = value
    elif option == '--future':
      future = value
      to = None
    else:
      assert False, 'unhandled command-line option'

  if to is not None:
    try:
      to = _parseDate(to)
    except ValueError:
      print >> sys.stderr, 'Can\'t parse date %s' % to
      return 1
  elif future is not None:
    try:
      future = int(future)
      if future < 0:
        raise ValueError()
    except ValueError:
      print >> sys.stderr, 'Invalid integer: %s' % future
      return 1
    to = from_ + datetime.timedelta(days=future)
  else:
    to = from_

  runner = runnerFactory()
  from Reminder import ShortcutReminder
  from contrib.deferrable.Reminder import DeferrableReminder
  def rem(*args, **kwargs):
    return runner.add(ShortcutReminder.fromString(*args, **kwargs))
  def deferrable(*args, **kwargs):
    return runner.add(DeferrableReminder.fromString(*args, **kwargs))
  for filename in args:
    execfile(filename, {
      'runner': runner,
      'rem': rem,
      'deferrable': deferrable,
    })
  runner.run(from_, to, mode)
  return 0


if __name__ == '__main__':
  sys.exit(main())
