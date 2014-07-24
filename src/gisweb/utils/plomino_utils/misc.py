#!/usr/bin/python
# -*- coding: utf-8 -*-

from DateTime import DateTime
from DateTime.interfaces import DateError

from Products.CMFPlomino.PlominoUtils import DateToString, StringToDate, json_loads

def StartDayofMonth(d):
    """ Returns the first day of the month
    d {DateTime}
    """
    # return DateTime(d.year(), d.month(), 1)
    return StringToDate(DateToString(d,'%m-%Y'),'%m-%Y')

def LastDayofMonth(d):
    """ Returns the last day of the month
    d {DateTime}
    """
    return StringToDate(DateToString(StartDayofMonth(d)+32,'%m-%Y'),'%m-%Y')-1

def _lookForValidDate(year, month, day, timeargs=[0, 0, 0], start=1):
    """ Please do not use directly. Use addToDate instead. """

    if month not in range(1, 13):
        raise Exception('GISWEB:UTILS ERROR: Not a valid month passed: %s' % month)

    if day not in range(1, 32):
        raise Exception('GISWEB:UTILS ERROR: Not a valid day passed: %s' % month)

    try:
        return DateTime(year, month, day, *timeargs) - start
    except DateError:
        # WARNING! only errors in day parameter are considered.
        day -= 1
        test = True
        while test:
            try:
                return DateTime(year, month, day, *timeargs)
            except DateError:
                day -= 1
            else:
                test = False

def addToDate(date, addend, units='months', start=1):
    """
    data: a zope DateTime object
    addend: int
    units: string, "months", "years" or "days" are accepted
    start: int, 0 or 1

    A DateTime may be added to a number and a number may be
    added to a DateTime and the number is supposed to represent a number of days
    to add to the date in the sum.
    You can use this function to easily add other time units such as months or years.
    For internal convention by default is returned the first valid date before the one
    you could expect.
    """

    if not isinstance(addend, int):
        addend = int(addend)

    if units == 'days':
        return date + addend

    year = date.year()
    month = date.month()
    day = date.day()

    timeargs = [date.hour(), date.minute(), date.second(), date.timezone()]
    months = range(1, 13)
    month_id = months.index(month)

    if units == 'months':
        new_year = year + (month_id+addend)/12
        mew_month_id = (month_id+addend)%12
        new_month = months[mew_month_id]
        return _lookForValidDate(new_year, new_month, day, timeargs, start=start)

    elif units == 'years':
        new_year = year + addend
        return _lookForValidDate(new_year, month, day, timeargs, start=start)

    else:
        raise Exception('units %s is not yet implemented' % units)

def is_json(s):
    try:
        json_loads(s)
    except ValueError:
        return False
    else:
        return True   