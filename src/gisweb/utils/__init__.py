#!/usr/bin/python
# -*- coding: utf-8 -*-
from AccessControl import allow_module, ModuleSecurityInfo
#from z3c.saconfig import named_scoped_session

allow_module('gisweb.utils')
allow_module('gisweb.utils.iride')
allow_module('gisweb.utils.iride.concessioni_strada')
allow_module('gisweb.utils.plominoKin')

def initialize(con):
    "Being a Zope2 Product we ensure this file will be imported at startup"

from xdocreport import report

import re

################################################################ PLOMINO ADDONS #

import plomino_addons

################################################################ PLOMINO UTILS #

from plomino_utils import attachThis, guessType
from plomino_utils import ondelete_parent, oncreate_child, onsave_child, ondelete_child, create_child
from plomino_utils import get_children_list, get_parent
from plomino_utils import get_docLinkInfo, get_aaData2
from plomino_utils import fetchDocs

from plomino_utils import StartDayofMonth
from plomino_utils import LastDayofMonth, addToDate, lookForValidDate
from plomino_utils import get_related_info
from plomino_utils import render_as_dataTable
from plomino_utils import get_dataFor, get_gridDataFor, renderRaw
from plomino_utils import getAllSubforms
from plomino_utils import serialItem, serialDoc
from plomino_utils import idx_createFieldIndex, getIndexType

################################################################### JSON UTILS #

from json_utils import json_dumps, json_loads


################################################################### ZOPE UTILS #

def aq_base(obj):
    return obj.aq_base()


#################################################################### ACL UTILS #

from acl_utils import get_users_info, getAllUserRoles, getUserPermissions


################################################################ UNICODEDAMMIT #

from UnicodeDammit import getUnicodeFrom


################################################################## PRINT UTILS #

from print_utils import plominoPrint


#################################################################### PDF UTILS #

from pdf_utils import generate_pdf


##################################################################### DB UTILS #

try:
    import sqlalchemy
    import z3c.saconfig
except ImportError:
    pass
else:
    # We're ok without those in case sqlalchemy is not available
    from db_utils import get_session, get_soup, plominoSqlSync, execute_sql
    from db_utils import suggestFromTable


############################################################### CF P.IVA UTILS #

from anagrafica_utils import is_valid_cf, is_valid_piva, cf_build


#################################################################### URL UTILS #

from url_utils import proxy, urllib_urlencode, requests_post

from urllib import urlencode
from urllib2 import urlopen
def openUrl(url, timeout=None, **kwargs):
    data = urlencode(kwargs)
    error = ''
    try:
        out = urlopen(url, data, timeout=timeout).read()
    except Exception, err:
        error = str(err)
        return ('', error)
    else:
        return (out, '')


################################################################### MISC UTILS #

def Type(arg):
    return '%s' % type(arg)

#from design_utils import exportElementAsXML

def re_findall(what, where):
    return re.findall(r'%s' % what, where)

from StringValidator import isEmail, isEmpty

################################################################### DATE UTILS #

import locale
def strftime(date, format, custom_locale):
    '''
    '''
    err = None
    try:
        locale.setlocale(locale.LC_ALL, custom_locale)
    except Exception, err:
        pass
    return date.strftime(format), err


################################################################# SPEZIA UTILS #

from spezia_utils import protocolla_doc, protocolla


############################################################### WORKFLOW UTILS #

from workflow_utils import getChainFor, getStatesInfo, getTransitionsInfo, doActionIfAny, getInfoFor, updateRoleMappingsFor, updateAllRoleMappingsFor


##################################################################### FS UTILS #

from fs_utils import os_listdir, os_path_join


################################################################### PLONE UTILS #

from plone_utils import sendMail

import os, subprocess

def getcwd():
    return os.getcwd()

def isRepoUpToDate(path):
    """
    0 : repo surely up to date
    1 : indexes do not correspond, maybe you need an upgrade
    """
    fullpath = os.path.join(os.getcwd(), path)
    command = 'git diff-index HEAD --quiet'
    p = subprocess.Popen(command.split(' '), cwd=fullpath)
    return '%s' % p.wait()
    
def getRepoRemotes(path):
    """
    returns the list of repositories you can get with "git remote -v"
    """
    fullpath = os.path.join(os.getcwd(), path)
    command = 'git remote -v'
    p = subprocess.Popen(command.split(' '), cwd=fullpath, stdout=subprocess.PIPE)
    result = [i.strip() for i in p.stdout.readlines()]
    p.wait()
    return result

#def popopen(command)


################################################################### IRIDE UTILS #

from iride import procedimento_pratica, inserisci_protocollo, lista_procedimenti, leggi_documento