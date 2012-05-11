#!/usr/bin/python
# -*- coding: utf-8 -*-
from AccessControl import allow_module
from Products.CMFPlomino.interfaces import IPlominoDatabase
from z3c.saconfig import named_scoped_session

from Products.CMFCore.utils import getToolByName
from zope.app.component.hooks import getSite

allow_module('gisweb.utils')

def initialize(con):
    "Being a Zope2 Product we ensure this file will be imported at startup"


################################################################ PLOMINO UTILS #

def get_parent_plominodb(obj):
    current = obj
    while hasattr(current, 'aq_parent') and not IPlominoDatabase.providedBy(current):
        current = current.aq_parent
    return hasattr(current, 'aq_parent') and current

def search_around(plominoDocument, parentKey='parentDocument', *targets, **filters):
    '''
    DA TESTARE
    
    "out" è un dizionario la cui chiavi sono le stringhe contenute in target se
    per esse è stato trovato almeno un valore tra i documenti collegati al
    plominoDocument (compreso lo stesso). Se i valori trovati per la chiave
    richiesta fossero più di uno questi vengono messi in una lista. Per ottenere
    meno valori è possibile affinare la ricerca fornendo le chiavi "filters" che
    vengono usate per le ricerche nel plominoIndex e per la selezione dei
    documenti da cui attingere i valori.
    ATTENZIONE! NON sono contemplate condizioni di confronto per le ricerche che
    siano più complesse del semplice confronto di uguaglianza. Possono però
    essere passati parametri specifici per la ricerca su ZDB quali "sort_on",
    "sort_order" e simili.
    
    può sostituire in maniera meno statica il get_info_pratica
    '''

    out = dict()
    if plominoDocument.isNewDocument(): return out

#    main_fields = [t for t in targets if t in plominoDocument.getForm().getFormFields()]
#    other_fields = [t for t in targets if t not in main_fields]
    
    items = plominoDocument.getItems()
    # cerco prima nel documento "genitore"
    for target in target:
        if target in items:
            out[target] = plominoDocument.getItem(target)
    
    # poi cerco nei documenti figli
    plominoIndex = plominoDocument.getParentDatabase().getIndex()
    filters[parentKey] = plominoDocument.id
    res = plominoIndex.dbsearch(**filters)
    for rec in res:
        pd = rec.getObject()
        
        # nel caso le chiavi in filters non fossero state indicizzate
        #+ evito i documenti che sarebbero stati scartati dalla ricerca
        if all([pd.getItem(k)==filters.get(k) for k in pd.getForm().getFormFields() if k in filters]):

            items = pd.getItems()
            for target in target:
                if target in items:
                    if target in out:
                        out[target] += [plominoDocument.getItem(target)]
                    else:
                        out[target] = [plominoDocument.getItem(target)]
            if len(out[target]) == 1:
                out[target] = out[target][0]

    return out

##################################################################### DB UTILS #

def get_something_from_db():
    session = get_session('maciste')
    # do something with session
    return "pluto"

def get_session(sessionname):
    "Use collective.saconnect to configure connections TTW"
    factory = named_scoped_session(sessionname)
    return factory()


################################################################### JSON UTILS #

import simplejson as json
def json_dumps(pyobj=''):
    return json.dumps(pyobj)

def json_loads(string, **kwargs):
    return json.loads(string, **kwargs)


################################################################### ZOPE UTILS #

def aq_base(obj):
    return obj.aq_base()


#################################################################### ACL UTILS #

def get_users_info(id_list, properties=('fullname', )):
    '''
    get an id_list as returned by the plominoDatabase method getUsersForRoles
    that maybe it's a principals id list in wich users id and groups id are not
    distinguished and return the list of specified properties from ACL.
    
    out = [{'id':..., 'fullname':...}, {...}, ...]
    
    '''
    
    context = getSite()
    
    acl_tool = getToolByName(context, 'acl_users')
    pg_tool = getToolByName(context, 'portal_groups')

    users = [acl_tool.getUserById(i) for i in id_list if acl_tool.getUserById(i)]
    groups = [pg_tool.getGroupById(i) for i in id_list if pg_tool.getGroupById(i)]
    
    members_in_groups = []
    for group in groups:
        members_in_groups += group.getGroupMembers()

    out = list()
    ids = list()
    
    for user in users+members_in_groups:
        myuser = dict()
        if hasattr(user.aq_base, 'getName'):
            user_id = user.getName()
        else:
            user_id = user.getProperty('id')
            
        if user_id not in ids:
            ids.append(user_id)
            myuser['id'] = user_id
            for prop in properties:
                myuser[prop] = user.getProperty(prop)
            out.append(myuser)
    
    return out
    
    
################################################################## PRINT UTILS #

import cStringIO, os
import xhtml2pdf.pisa as xhtml2pdf
from xhtml2pdf.default import DEFAULT_CSS as pisa_css

def plominoPrint(plominoDocument, form_name, default_css=None, use_command=False):
    form = plominoDocument.getParentDatabase().getForm(form_name)
    html_content = plominoDocument.openWithForm(form)
    
    if default_css:
        default_css = pisa_css + default_css

    rel_path = '..'
    abs_path = '%s' % plominoDocument.getParentDatabase().absolute_url()
    html_content = html_content.replace(rel_path, abs_path)

    if use_command:
        SRC = '/tmp/test_in.html'
        input_file = open(SRC, 'w')
        input_file.write(html_content)
        input_file.close()
        xml = os.popen("xhtml2pdf %s -" % SRC).read()
        os.remove(SRC)
#        output_file = open('/tmp/test_out.pdf', 'w')
#        output_file.write(xml)
#        output_file.close()
    else:
        pdf = xhtml2pdf.CreatePDF(
            html_content,
            default_css=default_css,
            )
        xml = pdf.dest.getvalue()
    
    return xml


############################################################### CF P.IVA UTILS #

def is_valid_cf(cf):

    cf = str(cf)

    if len(cf) <> 16: return False

    alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    odd_conv = {
        '0': 1, '1': 0, '2': 5, '3': 7, '4': 9, '5': 13, '6': 15, '7': 17,
        '8': 19, '9': 21,
        'A': 1, 'B': 0, 'C': 5, 'D': 7, 'E': 9, 'F': 13, 'G': 15, 'H': 17,
        'I': 19, 'J': 21, 'K': 2, 'L': 4, 'M': 18, 'N': 20, 'O': 11, 'P': 3,
        'Q': 6, 'R': 8, 'S': 12, 'T': 14, 'U': 16, 'V': 10, 'W': 22, 'X': 25,
        'Y': 24, 'Z': 23
    }
    
    even_conv = {
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
        '8': 8, '9': 9,
        'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7, 'I': 8,
        'J': 9, 'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15, 'Q': 16,
        'R': 17, 'S': 18, 'T': 19, 'U': 20, 'V': 21, 'W': 22, 'X': 23, 'Y': 24,
        'Z': 25
    }
    
    s = 0
    for char in cf[:-1][1::2]:
        s += even_conv[char.upper()]
    for char in cf[:-1][::2]:
        s += odd_conv[char.upper()]
        
    r = s%26
    
    r1 = alpha[r]
    
    return cf[-1].upper()==r1
    
def is_valid_piva(piva):
    
    piva = str(piva)
    if len(piva) <> 11: return False
    
    s = 0
    for char in piva[:-1][::2]:
        s += int(char)
    for char in piva[:-1][1::2]:
        x = 2*int(char)
        if x>9: x = x-9
        s += x
    
    r = s%10
    
    c = str(10-r)[-1]
    
    return piva[-1]==c
    

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

