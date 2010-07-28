import datetime
import re


def lastDayOfMonth(year, month):
  if month == 12:
    year = year+1
    month = 1
  else:
    month = month+1
  return datetime.date(year, month, 1) - datetime.timedelta(days=1)


class UnsafeDate(object):

  def __init__(self, year, month, day):
    super(UnsafeDate, self).__init__()
    self.year = year
    self.month = month
    self.day = day

  @staticmethod
  def fromDate(date):
    return UnsafeDate(date.year, date.month, date.day)

  def __cmp__(self, other):
    if self.year < other.year: return -1
    elif self.year > other.year: return 1
    if self.month < other.month: return -1
    elif self.month > other.month: return 1
    return self.day - other.day

  def __lt__(self, other):
    return self.__cmp__(other) < 0
  def __le__(self, other):
    return self.__cmp__(other) <= 0
  def __eq__(self, other):
    return self.__cmp__(other) == 0
  def __ne__(self, other):
    return self.__cmp__(other) != 0
  def __ge__(self, other):
    return self.__cmp__(other) >= 0
  def __gt__(self, other):
    return self.__cmp__(other) > 0


class NonExistingDaysHandling:
  WRAP = 0
  SKIP = 1
  RAISE = 2

def wrapDate(unsafeDate, nonexistingDaysHandling=NonExistingDaysHandling.WRAP):
  try:
    return datetime.date(unsafeDate.year, unsafeDate.month, unsafeDate.day)
  except ValueError:
    case = nonexistingDaysHandling
    enum = NonExistingDaysHandling
    if case == enum.WRAP:
      return lastDayOfMonth(unsafeDate.year, unsafeDate.month)
    elif case == enum.SKIP:
      return None
    elif case == enum.RAISE:
      raise

# returns tuple (date, skip)
def wrapDate_noFail(unsafeDate, nonexistingDaysHandling):
  date = wrapDate(unsafeDate, nonexistingDaysHandling=NonExistingDaysHandling.WRAP)
  if date is None:
    return (lastDayOfMonth(unsafeDate.year, unsafeDate.month), True)
  else:
    return (date, False)


ISO_DATE_REGEXP = re.compile('(\d+)-(\d+)-(\d+)$')
def parseIsoDate(string):
  m = ISO_DATE_REGEXP.match(string)
  return None if m is None \
    else UnsafeDate(*(int(group) for group in m.groups()))
