# -*- coding: utf-8 -*-

'''При запуске из командной строки запускает все unit-тесты,
объявленные в пакете C{rempy.contrib.deferred}.  Создан просто для удобства.
'''

from DateCondition import DeferrableDateCondition
from StringParser import DeferrableParser

import unittest


def additional_tests():
  '''Получить экземпляр класса C{unittest.TestSuite} со всеми тестами

  @returns: экземпляр класса C{unittest.TestSuite}
  '''
  subsuites = []
  loader = unittest.TestLoader()
  testCases = [
    DeferrableDateCondition.Test,
    DeferrableParser.Test,
  ]
  for testCase in testCases:
    subsuites.append(loader.loadTestsFromTestCase(testCase))
  return unittest.TestSuite(subsuites)

if __name__ == '__main__':
  unittest.TextTestRunner().run(additional_tests())
