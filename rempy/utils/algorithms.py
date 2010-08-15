# -*- coding: utf-8 -*-

'''Функции и классы, реализующие различные алгоритмы'''

def sortedUnique(mylist):
  '''Исключить дубликаты из отсортированного списка

  U{Источник<http://docs.python.org/faq/programming.html#how-do-you-remove-duplicates-from-a-list>}
  '''
  if mylist == []:
    return
  last = mylist[-1]
  for i in xrange(len(mylist)-2, -1, -1):
    if last == mylist[i]:
      del mylist[i]
    else:
      last = mylist[i]
