from AccessControl import allow_module
from Products.CMFPlomino.interfaces import IPlominoDatabase
from z3c.saconfig import named_scoped_session

allow_module('gisweb.utils')

def initialize(con):
    "Being a Zope2 Product we ensure this file will be imported at startup"


def get_parent_plominodb(obj):
    current = obj
    while hasattr(current, 'aq_parent') and not IPlominoDatabase.providedBy(current):
        current = current.aq_parent
    return hasattr(current, 'aq_parent') and current


def get_something_from_db():
    session = get_session('maciste')
    # do something with session
    return "pluto"

def get_session(sessionname):
    "Use collective.saconnect to configure connections TTW"
    factory = named_scoped_session(sessionname)
    return factory()
