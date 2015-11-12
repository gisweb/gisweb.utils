# -*- coding: utf-8 -*-
# courtesy of http://code.activestate.com/recipes/66439-stringvalidator/
import re
true = True # 1
false = False # 0

class StringValidator:
    RE_ALPHA = None
    RE_ALPHANUMERIC = None
    RE_NUMERIC = None
    RE_EMAIL = None

    validateString = ""
    _patterns = {}

    def __init__(self, validateString):
        self.validateString = validateString

    def isAlpha(self):
        if not self.__class__.RE_ALPHA:
            self.__class__.RE_ALPHA = re.compile("^\D+$")
        return self.checkStringAgainstRe(self.__class__.RE_ALPHA)

    def isAlphaNumeric(self):
        if not self.__class__.RE_ALPHANUMERIC:
            self.__class__.RE_ALPHANUMERIC = re.compile("^[a-zA-Z0-9]+$")
        return self.checkStringAgainstRe(self.__class__.RE_ALPHANUMERIC)

    def isNumeric(self):
        if not self.__class__.RE_NUMERIC:
            self.__class__.RE_NUMERIC = re.compile("^\d+$")
        return self.checkStringAgainstRe(self.__class__.RE_NUMERIC)

    def isEmail(self):
        # coutesy of http://www.regular-expressions.info/email.html
        long_exp = "[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
        short_exp = "^.+@.+\..{2,3}$"
        if not self.__class__.RE_EMAIL:
            self.__class__.RE_EMAIL = re.compile(long_exp)
        return self.checkStringAgainstRe(self.__class__.RE_EMAIL)

    def isEmpty(self):
        return self.validateString == ""

    def definePattern(self, re_name, re_pat):
        self._patterns[re_name] = re_pat

    def isValidForPattern(self, re_name):
        if self._patterns.has_key(re_name):
            if type(self._patterns[re_name]) == type(''):
                self._patterns[re_name] = re.compile(self._patterns[re_name])
                return self.checkStringAgainstRe(self._patterns[re_name])
        else:
            raise KeyError, "No pattern name '%s' stored."

    # this method should be considered to be private (not be be used via interface)
    def checkStringAgainstRe(self, regexObject):
        if regexObject.search(self.validateString) == None:
            return false
        return true

def isEmail(string):
    return StringValidator(string).isEmail()

def isEmpty(string):
    return StringValidator(string).isEmpty()

# example usage

#sv1 = StringValidator("joe@testmail.com")
#sv2 = StringValidator("rw__343")

#if sv1.isEmail(): print sv1.validateString + " is a valid e-mail address"
#else: print sv1.validateString + " is not a valid e-mail address"

#if sv2.isAlphaNumeric(): print sv2.validateString + " is a valid alpha-numeric string"
#else: print sv2.validateString + "i is not a valid alpha-numeric string"
