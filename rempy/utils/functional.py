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


def find_if(iterable, unary_predicate):
  for i in iterable:
    if unary_predicate(i):
      return i
  return None


def find_not_if(iterable, unary_predicate):
  return find_if(iterable, lambda i: not unary_predicate(i))
