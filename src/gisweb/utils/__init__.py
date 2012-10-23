#!/usr/bin/python
# -*- coding: utf-8 -*-
from AccessControl import allow_module
#from z3c.saconfig import named_scoped_session

allow_module('gisweb.utils')
allow_module('gisweb.utils.plominoKin')

def initialize(con):
    "Being a Zope2 Product we ensure this file will be imported at startup"


################################################################ PLOMINO UTILS #

from plomino_utils import get_parent_plominodb
from plomino_utils import attachThis
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

################################################################### JSON UTILS #

from json_utils import json_dumps, json_loads


################################################################### ZOPE UTILS #

def aq_base(obj):
    return obj.aq_base()


#################################################################### ACL UTILS #

from acl_utils import get_users_info

    
################################################################## PRINT UTILS #

from print_utils import plominoPrint
from print_utils import UnicodeDammit


#################################################################### PDF UTILS #

from pdf_utils import generate_pdf


##################################################################### DB UTILS #

from db_utils import get_session, plominoSqlSync
from db_utils import suggestFromTable


############################################################### CF P.IVA UTILS #

from anagrafica_utils import is_valid_cf, is_valid_piva


#################################################################### URL UTILS #

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

from spezia_utils import getXmlBody


################################################################### MAIL UTILS #

#def test_mail(to, mail_text=''):
#    import smtplib

#server = 'smtp.gmail.com'
#user = 'manuele.pesenti'
#password = 'p0TA31le'

#recipients = ['user@mail.com', 'other@mail.com']
#sender = 'manuele.pesenti@mail.com'
#message = 'Hello World'

#session = smtplib.SMTP(server, '587')
## if your SMTP server doesn't need authentications,
## you don't need the following line:
#session.login(user, password)
#session.sendmail(sender, recipients, message)
#    #    host = getToolByName(context, 'MailHost')
#    #    sender = context.getProperty('email_from_address')
#    #    try:
#    #        host.send(html_message, mto=[to], mfrom=sender, 
#    #        subject=title, encode=None, 
#    #        immediate=False, charset='utf8', msg_type=None)
#    #    except Exception, error:
#    #        return str(error)
#    #    else:
#    #        return ''


############################################################# PERMISSION UTILS #

#def has_permission(cases, permission_store={}, form_name='', element_name='', permission_name=''):
#    '''
#    
#    DA TESTARE
#    
#    form_name: <plominoForm name>
#    element_name: <plominoAction name> or <plominoHidewhen name>
#    permission_name: <could be any string "read" "write" are the most used>

#    cases = [dict(ruolo='', status='')]

#    permission_store = {
#        'form_name|element_name|permission_name': dict(
#            ruolo = lambda x: x in (..., ) # <- permission definition
#            status = lambda y: y not in (..., ) # <- permission definition
#        )
#    }
#    '''

#    permission_key = '|'.join((form_name, element_name, permission_name, ))

#    all_possible_keys = ['|'.join([a, b])
#        for a in (form_name, '')
#        for b in (element_name, '')]

#    #possible_keys = [k for k in all_possible_keys if k in permission_store]

#    possible_keys = [k for k in permission_store if k.split('|')[:2] in [v.split('|') for v in all_possible_keys]]

#    if not possible_keys: return True 

#    for k in possible_keys:
#        if k.split('|')[2] in ('', 'any', permission_name, ):
#            permission = permission_store.get(k)
#            if not permission: return True # No permissions setted up about your case. You pass the guard!
#            for case in cases:
#                ruolo = case.get('ruolo') or ''
#                status = case.get('status') or ''
#                if permission(ruolo, status): return True # If just one condition specified is satified you pass the guard.

#    return False
