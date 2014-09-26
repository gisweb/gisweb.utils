#!/usr/bin/python
# -*- coding: utf-8 -*-
from AccessControl import allow_module, ModuleSecurityInfo
#from z3c.saconfig import named_scoped_session

allow_module('gisweb.utils')
allow_module('gisweb.utils.dev_utils.utils')
allow_module('gisweb.utils.plomino_utils.dev')


def initialize(con):
    "Being a Zope2 Product we ensure this file will be imported at startup"

################################################################ PLOMINO ADDONS #

import plomino_addons

################################################################ PLOMINO UTILS #

from plomino_utils.utils import attachThis, getIndexType
from plomino_utils.utils import serialItem, serialDoc, getItems

from plomino_utils.misc import addToDate, LastDayofMonth, is_json
from plomino_utils.misc import idx_createFieldIndex
from plomino_utils.design import updateAllXML, addLabelsField
from plomino_utils.design import exportElementAsXML, importElementFromXML

from plomino_report import report
################################################################### ZOPE UTILS #

def aq_base(obj):
    return obj.aq_base()


#################################################################### ACL UTILS #

from acl_utils import get_users_info, getAllUserRoles, getUserPermissions, getRolesOfPermission


################################################################ UNICODEDAMMIT #

from UnicodeDammit import getUnicodeFrom


############################################################### CF P.IVA UTILS #

from anagrafica_utils import is_valid_cf, is_valid_piva, cf_build


#################################################################### URL UTILS #

from url_utils import proxy, urllib_urlencode, requests_post,get_headers
from url_utils import urllib_quote_plus, geocode, wsquery,requests_get, myproxy
from url_utils import encode_b64, decode_b64

def openUrl(url, timeout=None, **kwargs):
    from urllib import urlencode
    from urllib2 import urlopen
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

def re_findall(what, where):
    from re import findall
    return findall(r'%s' % what, where)

from StringValidator import isEmail, isEmpty
from XmlDict import XmlDictConfig


############################################################### WORKFLOW UTILS #

from workflow_utils import getChainFor, getStatesInfo, getTransitionsInfo
from workflow_utils import doActionIfAny, getInfoFor, updateAllRoleMappingsFor


##################################################################### FS UTILS #

from fs_utils import os_listdir, os_path_join, os_path_isfile


################################################################### XML UTILS #

from XmlDict import parseXML


################################################################### PLONE UTILS #

from plone_utils import sendMail, importFromPortal, forceDelete, guessType

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


############################################################ GPOLYENCODE UTILS #

from gpolyencode_utils import gpoly_encode, decode_line


######################################################################### TEST #

def getErrorMessage(exception):
    return dict(
        type = type(exception),
        message = exception.message
    )

oVars = lambda o: vars(o)

def set_trace(context, *args, **kwargs):
    """ """
    try:
        import pdb; pdb.set_trace()
    except ImportError:
        import ipdb; ipdb.set_trace()

from zope.security import checkPermission
def checkpermission(context, perm):
    return checkPermission(perm, context)
