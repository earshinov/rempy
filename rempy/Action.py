'''Содержит иерархию классов L{Action}'''

class Action:
  '''Базовый класс для классов, реализующих действия, которые выполняются,
  когда для напоминалки находится подходящая дата.  Фактически, просто
  callable, а класс объявляется просто для удобства документирования.'''

  def __call__(self, date):
    '''Выполнить связанное с объектом действие для заданной даты

    @param date: объект класса C{datetime.date}
    '''
    pass


class MessagePrinter(Action):
  '''Выполняет вывод заданного сообщения'''

  def __init__(self, message):
    '''Конструктор

    @param message: строка сообщения
    '''
    super(MessagePrinter, self).__init__()
    self.message = message

  def __call__(self, date):
    print(self.message)
