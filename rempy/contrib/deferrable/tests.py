# -*- coding: utf-8 -*-

'''При запуске из командной строки запускает все unit-тесты,
объявленные в пакете C{rempy.contrib.deferred}.  Создан просто для удобства.
'''

from DateCondition import DeferrableDateCondition
from StringParser import DeferrableParser

import unittest

if __name__ == '__main__':
  subsuites = []
  loader = unittest.TestLoader()
  testCases = [
    DeferrableDateCondition.Test,
    DeferrableParser.Test,
  ]
  for testCase in testCases:
    subsuites.append(loader.loadTestsFromTestCase(testCase))
  suite = unittest.TestSuite(subsuites)
  unittest.TextTestRunner().run(suite)
