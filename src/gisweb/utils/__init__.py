from AccessControl import allow_module
from Products.CMFPlomino.interfaces import IPlominoDatabase

allow_module('gisweb.utils')

def initialize(con):
    "Being a Zope2 Product we ensure this file will be imported"


def get_parent_plominodb(obj):
    current = obj
    while hasattr(current, 'aq_parent') and not IPlominoDatabase.providedBy(current):
        current = current.aq_parent
    return current

