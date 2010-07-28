import datetime
import getopt
from heapq import heappop, heappush
import sys

import utils.dates as dateutils


class RunnerMode:
  REMIND = 0
  EVENTS = 1


class Runner(object):

  def __init__(self):
    super(Runner, self).__init__()
    self.reminders = []

  def add(self, reminder):
    self.reminders.append(reminder)

  def run(self, fromDate, toDate, mode):

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
      gen = reminder.condition(mode).scan(fromDate)
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
    pass

  def _executeReminder(self, reminder, date):
    pass


class PrintRunner(Runner):

  def _handleNextDate(self, date):
    print 'Reminders for %s' % date.isoformat()

  def _executeReminder(self, reminder, date):
    reminder.execute(date)


def main(args, runnerFactory=PrintRunner):
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
      from_ = dateutils.parseIsoDate(value)
      if from_ is None:
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
    to = dateutils.parseIsoDate(to)
    if to is None:
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
