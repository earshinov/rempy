# -*- coding: utf-8 -*-

'''Функции для программирования «в функциональном стиле»'''

def all(iterable, unary_predicate):
  for i in iterable:
    if not unary_predicate(i):
      return False
  return True


def any(iterable, unary_predicate):
  for i in iterable:
    if unary_predicate(i):
      return True
  return False
