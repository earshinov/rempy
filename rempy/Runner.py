# -*- coding: utf-8 -*-

'''Содержит иерархию классов L{Runner} и функцию L{main}

При запуске из командной строки запускает функцию L{main}.'''

import datetime
import getopt
from heapq import heappop, heappush
import sys

import utils.dates as dateutils


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

    def __pushNextEvent(reminder, gen):
      to = toDate + datetime.timedelta(days=reminder.advanceWarningValue()) \
        if mode == RunnerMode.REMIND else toDate
      try:
        date = gen.next()
      except StopIteration:
        return
      if date <= to:
        heappush(heap, (date, reminder, gen))

    for reminder in self.reminders:
      gen = iter(reminder.condition(mode).scan(fromDate))
      __pushNextEvent(reminder, gen)
    currentDate = None
    while True: # until heap is empty and heappop() raises IndexError
      try:
        date, reminder, gen = heappop(heap)
      except IndexError:
        break
      if date != currentDate:
        currentDate = date
        self._handleNextDate(date)
      self._executeReminder(reminder, date)
      __pushNextEvent(reminder, gen)

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


def main(args, runnerFactory=PrintRunner):
  '''Функция main()

  @param args: Аргументы командной строки, включая первый, который задаёт имя команды
  @param runnerFactory: callable, при вызове без параметров возвращающий объект
    класса L{Runner}, который будет использоваться для запуска напоминалок
  '''
  assert len(args) > 0

  USAGE = '''Usage: %s COMMAND OPTIONS\n
COMMAND = { remind | events }
OPTIONS = [ --from=DATE ] [ --to=DATE | --future=N_DAYS ]
''' % args[0]

  if len(args) < 2:
    print >> sys.stderr, 'A command is required'
    print >> sys.stderr, USAGE
    exit(1)

  if args[1] == 'remind':
    mode = RunnerMode.REMIND
  elif args[1] == 'events':
    mode = RunnerMode.EVENTS
  else:
    print >> sys.stderr, 'Unknown command: "%s"' % args[1]
    print >> sys.stderr, USAGE
    exit(1)

  try:
    longopts = ['help', 'usage', 'from=', 'to=', 'future=']
    options, args = getopt.gnu_getopt(args[2:], 'h', longopts)
  except getopt.GetoptError, err:
    print >> sys.stderr, `err`
    print >> sys.stderr, USAGE
    exit(1)

  from_ = datetime.date.today()
  to = future = None
  for option, value in options:
    if option in ('-h', '--help', '--usage'):
      print USAGE
      exit()
    elif option == '--from':
      try:
        from_ = dateutils.parseIsoDate(value)
      except ValueError:
        print >> sys.stderr, 'Can\'t parse date %s' % value
        exit(1)
      from_ = dateutils.wrapDate(from_)
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
      to = dateutils.parseIsoDate(to)
    except ValueError:
      print >> sys.stderr, 'Can\'t parse date %s' % to
      exit(1)
    to = dateutils.wrapDate(to)
  elif future is not None:
    try:
      future = int(future)
      if future < 0:
        raise ValueError()
    except ValueError:
      print >> sys.stderr, 'Invalid integer: %s' % future
      exit(1)
    to = from_ + datetime.timedelta(days=future)
  else:
    to = from_

  runner = runnerFactory()
  for filename in args:
    execfile(filename, {'runner': runner})
  runner.run(from_, to, mode)


if __name__ == '__main__':
  main(sys.argv)
