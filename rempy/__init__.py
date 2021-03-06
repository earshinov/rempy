'''
Пакет предоставляет классы и функции для задания напоминалок и поиска дат,
на которые они выпадают.

Типичный вариант использования: создать объект класса L{Runner<Runner.Runner>},
добавить в него с помощью метода L{Runner.add<Runner.Runner.add>} объекты класса
L{Reminder<Reminder.Reminder>} и получить список активных напоминалок для
заданного диапазона дат, используя метод L{Runner.run<Runner.Runner.run>}.

Классы, размещённые в этом пакете позволяют использовать в напоминалках только
условия, связанные с датой.  Дополнительная функциональность (например,
поддержка напоминаний с заданным временем) размещается в отдельных пакетах, как
правило внутри пакета L{rempy.contrib}.  Это позволяет отделить базовую
функциональность от расширений, что как минимум делает код более понятным.
'''

__version__ = '0.3-20181028'
