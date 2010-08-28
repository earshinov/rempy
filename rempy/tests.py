# -*- coding: utf-8 -*-

'''При запуске из командной строки запускает все unit-тесты,
объявленные в пакете и подпакетах.  Создан просто для удобства.
'''

import DateCondition
import StringParser
import utils.dates as dateutils
import contrib.deferrable.tests

import unittest


def additional_tests():
  '''Получить экземпляр класса C{unittest.TestSuite} со всеми тестами

  @returns: экземпляр класса C{unittest.TestSuite}
  '''
  subsuites = [
    contrib.deferrable.tests.additional_tests(),
  ]
  loader = unittest.TestLoader()
  testCases = [
    DateCondition.SimpleDateCondition.Test,
    DateCondition.RepeatDateCondition.Test,
    DateCondition.ShiftDateCondition.Test,
    DateCondition.SatisfyDateCondition.Test,
    DateCondition.CombinedDateCondition.Test,
    StringParser.DateConditionParser.Test,
    StringParser.ReminderParser.Test,
    dateutils._Test_dayOfYear,
    dateutils._Test_isoweekno,
    dateutils._Test_weekno,
  ]
  for testCase in testCases:
    subsuites.append(loader.loadTestsFromTestCase(testCase))
  return unittest.TestSuite(subsuites)

if __name__ == '__main__':
  unittest.TextTestRunner().run(additional_tests())
