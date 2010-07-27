import DateCondition

import unittest

if __name__ == '__main__':
  subsuites = []
  loader = unittest.TestLoader()
  testCases = [
    DateCondition.DateCondition.Test_fromString,
    DateCondition.SimpleDateCondition.Test,
    DateCondition.RepeatDateCondition.Test,
    DateCondition.SatisfyDateCondition.Test,
    DateCondition.CombinedDateCondition.Test,
  ]
  for testCase in testCases:
    subsuites.append(loader.loadTestsFromTestCase(testCase))
  suite = unittest.TestSuite(subsuites)
  unittest.TextTestRunner().run(suite)
