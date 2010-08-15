# -*- coding: utf-8 -*-

'''При запуске из командной строки запускает все unit-тесты,
объявленные в пакете C{rempy}.  Создан просто для удобства.
'''

import DateCondition
import StringParser
import utils.dates as dateutils

import unittest


if __name__ == '__main__':
  subsuites = []
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
  suite = unittest.TestSuite(subsuites)
  unittest.TextTestRunner().run(suite)
