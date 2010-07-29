class Action(object):

  def __call__(self, date):
    pass


class MessagePrinter(Action):

  def __init__(self, message):
    super(MessagePrinter, self).__init__()
    self.message = message

  def __call__(self, date):
    print self.message
