# <http://docs.python.org/faq/programming.html#how-do-you-remove-duplicates-from-a-list>
def sortedUnique(mylist):
  if mylist == []:
    return
  last = mylist[-1]
  for i in xrange(len(mylist)-2, -1, -1):
    if last == mylist[i]:
      del mylist[i]
    else:
      last = mylist[i]
