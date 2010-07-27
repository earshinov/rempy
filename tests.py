import DateCondition
import StringParser

import unittest

if __name__ == '__main__':
  subsuites = []
  loader = unittest.TestLoader()
  testCases = [
    DateCondition.SimpleDateCondition.Test,
    DateCondition.RepeatDateCondition.Test,
    DateCondition.SatisfyDateCondition.Test,
    DateCondition.CombinedDateCondition.Test,
    StringParser.DateConditionParser.Test,
  ]
  for testCase in testCases:
    subsuites.append(loader.loadTestsFromTestCase(testCase))
  suite = unittest.TestSuite(subsuites)
  unittest.TextTestRunner().run(suite)
